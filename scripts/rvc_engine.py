"""
rvc_engine.py
─────────────
fairseq 의존성 없이 순수 PyTorch + Transformers + Parselmouth/TorchCrepe 기반으로
RVC v2 모델(.pth 및 .index)을 고속으로 추론하는 독립형 음성 변환 엔진.
"""

import math
import sys
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from torch.nn import functional as F
from torch.nn.utils import weight_norm, remove_weight_norm
import soundfile as sf
import librosa
import parselmouth
import faiss

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════
# 1. RVC v2 신경망 아키텍처 (NSF-HiFiGAN & Synthesizer)
# ══════════════════════════════════════════════════════════════════

LRELU_SLOPE = 0.1

def init_weights(m, mean=0.0, std=0.01):
    classname = m.__class__.__name__
    if classname.find("Conv") != -1:
        m.weight.data.normal_(mean, std)

def get_padding(kernel_size, dilation=1):
    return int((kernel_size * dilation - dilation) / 2)


def parse_sr(sr_val):
    if isinstance(sr_val, str):
        s = sr_val.lower().strip()
        if 'k' in s:
            return int(float(s.replace('k', '')) * 1000)
        return int(float(s))
    return int(sr_val)


class SineGen(nn.Module):
    def __init__(self, samp_rate, harmonic_num=0, sine_amp=0.1, noise_std=0.003, voiced_threshold=0):
        super().__init__()
        self.sine_amp = sine_amp
        self.noise_std = noise_std
        self.harmonic_num = harmonic_num
        self.dim = self.harmonic_num + 1
        self.sampling_rate = parse_sr(samp_rate)
        self.voiced_threshold = voiced_threshold

    def _f02uv(self, f0):
        uv = torch.ones_like(f0)
        uv = uv * (f0 > self.voiced_threshold)
        return uv

    def forward(self, f0):
        with torch.no_grad():
            f0 = f0[:, None, :]
            f0_buf = torch.zeros(f0.shape[0], self.dim, f0.shape[2], device=f0.device)
            f0_buf[:, 0, :] = f0[:, 0, :]
            for idx in range(self.harmonic_num):
                f0_buf[:, idx + 1, :] = f0[:, 0, :] * (idx + 2)

            rad_values = (f0_buf / self.sampling_rate) % 1
            rand_ini = torch.rand(f0_buf.shape[0], f0_buf.shape[1], 1, device=f0.device)
            rand_ini[:, 0, :] = 0
            rad_values[:, :, 0] = rad_values[:, :, 0] + rand_ini[:, :, 0]

            tmp_over_one = torch.cumsum(rad_values, 2)
            tmp_over_one *= 2 * math.pi
            sine_waves = torch.sin(tmp_over_one) * self.sine_amp

            uv = self._f02uv(f0)
            noise_amp = uv * self.noise_std + (1 - uv) * self.sine_amp / 3
            noise = noise_amp * torch.randn_like(sine_waves)
            sine_waves = sine_waves * uv + noise
        return sine_waves


class SourceModuleHnNSF(nn.Module):
    def __init__(self, sample_rate, harmonic_num=0, sine_amp=0.1, noise_std=0.003, voiced_thresh=0):
        super().__init__()
        self.sine_amp = sine_amp
        self.noise_std = noise_std
        self.harmonic_num = harmonic_num
        self.dim = self.harmonic_num + 1
        self.sampling_rate = parse_sr(sample_rate)
        self.voiced_threshold = voiced_thresh
        self.sine_gen = SineGen(self.sampling_rate, harmonic_num, sine_amp, noise_std, voiced_thresh)
        self.linear = nn.Linear(self.dim, 1)

    def forward(self, f0):
        sine_wavs = self.sine_gen(f0)
        sine_wavs = sine_wavs.transpose(1, 2)
        sine_merge = self.linear(sine_wavs)
        return sine_merge.transpose(1, 2)


class ResBlock1(nn.Module):
    def __init__(self, channels, kernel_size=3, dilation=(1, 3, 5)):
        super().__init__()
        self.convs1 = nn.ModuleList([
            weight_norm(nn.Conv1d(channels, channels, kernel_size, 1, dilation=dilation[0],
                               padding=get_padding(kernel_size, dilation[0]))),
            weight_norm(nn.Conv1d(channels, channels, kernel_size, 1, dilation=dilation[1],
                               padding=get_padding(kernel_size, dilation[1]))),
            weight_norm(nn.Conv1d(channels, channels, kernel_size, 1, dilation=dilation[2],
                               padding=get_padding(kernel_size, dilation[2])))
        ])
        self.convs1.apply(init_weights)

        self.convs2 = nn.ModuleList([
            weight_norm(nn.Conv1d(channels, channels, kernel_size, 1, dilation=1,
                               padding=get_padding(kernel_size, 1))),
            weight_norm(nn.Conv1d(channels, channels, kernel_size, 1, dilation=1,
                               padding=get_padding(kernel_size, 1))),
            weight_norm(nn.Conv1d(channels, channels, kernel_size, 1, dilation=1,
                               padding=get_padding(kernel_size, 1)))
        ])
        self.convs2.apply(init_weights)

    def forward(self, x):
        for c1, c2 in zip(self.convs1, self.convs2):
            xt = F.leaky_relu(x, LRELU_SLOPE)
            xt = c1(xt)
            xt = F.leaky_relu(xt, LRELU_SLOPE)
            xt = c2(xt)
            x = xt + x
        return x

    def remove_weight_norm(self):
        for l in self.convs1:
            remove_weight_norm(l)
        for l in self.convs2:
            remove_weight_norm(l)


class GeneratorNSF(nn.Module):
    def __init__(self, initial_channel, resblock_kernel_sizes, resblock_dilation_sizes,
                 upsample_rates, upsample_initial_channel, upsample_kernel_sizes, gin_channels=256, sr=32000):
        super().__init__()
        self.num_kernels = len(resblock_kernel_sizes)
        self.num_upsamples = len(upsample_rates)
        self.f0_upsamp = nn.Upsample(scale_factor=math.prod(upsample_rates))
        self.m_source = SourceModuleHnNSF(sample_rate=sr, harmonic_num=0)
        self.conv_pre = nn.Conv1d(initial_channel, upsample_initial_channel, 7, 1, padding=3)

        self.ups = nn.ModuleList()
        self.noise_convs = nn.ModuleList()
        
        channels = upsample_initial_channel
        for i, (u, k) in enumerate(zip(upsample_rates, upsample_kernel_sizes)):
            c_cur = upsample_initial_channel // (2 ** (i + 1))
            self.ups.append(
                weight_norm(nn.ConvTranspose1d(channels, c_cur, k, u, padding=(k - u) // 2))
            )
            stride_cum = math.prod(upsample_rates[i + 1:]) if i + 1 < len(upsample_rates) else 1
            if stride_cum > 1:
                self.noise_convs.append(
                    nn.Conv1d(1, c_cur, kernel_size=stride_cum * 2, stride=stride_cum, padding=stride_cum // 2)
                )
            else:
                self.noise_convs.append(nn.Conv1d(1, c_cur, kernel_size=1))
            channels = c_cur

        self.resblocks = nn.ModuleList()
        for i in range(len(self.ups)):
            ch = upsample_initial_channel // (2 ** (i + 1))
            for j, (k, d) in enumerate(zip(resblock_kernel_sizes, resblock_dilation_sizes)):
                self.resblocks.append(ResBlock1(ch, k, d))

        self.conv_post = nn.Conv1d(ch, 1, 7, 1, padding=3, bias=False)
        self.ups.apply(init_weights)

        if gin_channels != 0:
            self.cond = nn.Conv1d(gin_channels, upsample_initial_channel, 1)

    def forward(self, x, f0, g=None):
        # f0: [B, T] -> [B, 1, T] -> [B, 1, T * scale] -> [B, T * scale]
        f0_upsampled = self.f0_upsamp(f0.unsqueeze(1)).squeeze(1)
        har_source = self.m_source(f0_upsampled)
        x = self.conv_pre(x)
        if g is not None:
            x = x + self.cond(g)

        for i in range(self.num_upsamples):
            x = F.leaky_relu(x, LRELU_SLOPE)
            x = self.ups[i](x)
            x_source = self.noise_convs[i](har_source)
            x = x + x_source[:, :, :x.shape[-1]]
            xs = None
            for j in range(self.num_kernels):
                if xs is None:
                    xs = self.resblocks[i * self.num_kernels + j](x)
                else:
                    xs += self.resblocks[i * self.num_kernels + j](x)
            x = xs / self.num_kernels
        x = F.leaky_relu(x)
        x = self.conv_post(x)
        x = torch.tanh(x)
        return x

    def remove_weight_norm(self):
        for l in self.ups:
            remove_weight_norm(l)
        for l in self.resblocks:
            l.remove_weight_norm()


f0_bin = 256
f0_max = 1100.0
f0_min = 50.0
f0_mel_min = 1127 * np.log(1 + f0_min / 700)
f0_mel_max = 1127 * np.log(1 + f0_max / 700)


def f0_to_coarse(f0):
    f0_mel = 1127 * np.log(1 + f0 / 700)
    f0_mel[f0_mel > 0] = (f0_mel[f0_mel > 0] - f0_mel_min) * (f0_bin - 2) / (f0_mel_max - f0_mel_min) + 1
    f0_mel[f0_mel <= 1] = 1
    f0_mel[f0_mel > (f0_bin - 1)] = f0_bin - 1
    f0_coarse = np.rint(f0_mel).astype(np.int64)
    return f0_coarse


class SynthesizerTrnMs768NSFsid(nn.Module):
    """RVC v2 768차원 모델 디코더"""
    def __init__(self, spec_channels, segment_size, inter_channels, hidden_channels,
                 filter_channels, n_heads, n_layers, kernel_size, p_dropout, resblock,
                 resblock_kernel_sizes, resblock_dilation_sizes, upsample_rates,
                 upsample_initial_channel, upsample_kernel_sizes, spk_embed_dim,
                 gin_channels, sr, **kwargs):
        super().__init__()
        self.dec = GeneratorNSF(
            inter_channels, resblock_kernel_sizes, resblock_dilation_sizes,
            upsample_rates, upsample_initial_channel, upsample_kernel_sizes,
            gin_channels=gin_channels, sr=sr
        )
        self.enc_p = nn.Linear(768, inter_channels)
        self.emb_g = nn.Embedding(spk_embed_dim, gin_channels)
        self.emb_pitch = nn.Embedding(256, inter_channels)

    def forward(self, phone, phone_lengths, pitch, pitchf, sid):
        g = self.emb_g(sid).unsqueeze(-1)
        x = self.enc_p(phone)
        if pitch is not None and hasattr(self, "emb_pitch"):
            x = x + self.emb_pitch(pitch)
        x = x.transpose(1, 2)
        o = self.dec(x, pitchf, g=g)
        return o


# ══════════════════════════════════════════════════════════════════
# 2. 고속 RVC 추론 클래스
# ══════════════════════════════════════════════════════════════════

class RVCStandaloneInfer:
    def __init__(self, model_path: Path, index_path: Path = None, device: str = "cuda:0"):
        self.device = torch.device(device if torch.cuda.is_available() and "cuda" in device else "cpu")
        print(f"🧠 RVC 독립형 추론 엔진 로딩 중... (디바이스: {self.device})")

        # 1. 모델 가중치 로드
        cpt = torch.load(str(model_path), map_location="cpu")
        self.target_sr = parse_sr(cpt.get("sr", 32000))
        self.f0 = cpt.get("f0", 1)
        self.version = cpt.get("version", "v2")
        self.config = cpt.get("config", [])

        # 2. 모델 인스턴스화
        self.net_g = SynthesizerTrnMs768NSFsid(
            *self.config[:17],
            sr=self.target_sr
        )
        self.net_g.load_state_dict(cpt["weight"], strict=False)
        self.net_g.eval().to(self.device)
        if hasattr(self.net_g.dec, "remove_weight_norm"):
            try:
                self.net_g.dec.remove_weight_norm()
            except Exception:
                pass

        # 3. HuBERT Feature Extractor (torchaudio HUBERT_BASE)
        print("📥 Torchaudio HuBERT 특징 추출기 로드 중...")
        import torchaudio
        bundle = torchaudio.pipelines.HUBERT_BASE
        self.hubert = bundle.get_model().to(self.device)
        self.hubert.eval()

        # 4. FAISS 인덱스 로드 (선택 사항)
        self.index = None
        if index_path and Path(index_path).exists():
            try:
                print(f"📑 FAISS Index 로드: {Path(index_path).name}")
                self.index = faiss.read_index(str(index_path))
            except Exception as e:
                print(f"⚠️ Index 로드 실패: {e}")

    def extract_f0_pm(self, x, sr, f0_up_key=0):
        """Parselmouth 기반 100Hz F0 추출 (10ms hop)"""
        time_step = 160 / 16000
        sound = parselmouth.Sound(x, sr)
        pitch = sound.to_pitch_ac(
            time_step=time_step,
            voicing_threshold=0.6,
            pitch_floor=f0_min,
            pitch_ceiling=f0_max,
        )
        pitch_values = pitch.selected_array["frequency"].copy()
        
        # 키 이동
        if f0_up_key != 0:
            pitch_values = pitch_values * (2 ** (f0_up_key / 12.0))
        return pitch_values

    def convert(self, input_wav_path: Path, output_wav_path: Path,
                f0_up_key: int = 0, index_rate: float = 0.6):
        # 1. 입력 오디오 로드 (16kHz 변환)
        wav, sr = librosa.load(str(input_wav_path), sr=16000)

        # 2. HuBERT 특징 추출 (50Hz -> 100Hz repeat_interleave 2x)
        with torch.no_grad():
            inp = torch.from_numpy(wav).unsqueeze(0).float().to(self.device)
            feats, _ = self.hubert.extract_features(inp)
            feat = feats[-1].squeeze(0) # [T_50, 768]
            
            # FAISS 음색 인덱스 검색 및 블렌딩
            if self.index is not None and index_rate > 0:
                try:
                    feat_np = feat.cpu().numpy().astype(np.float32)
                    _, I = self.index.search(feat_np, 1)
                    idx_feat = self.index.reconstruct_n(0, self.index.ntotal)[I.squeeze()]
                    feat = (1 - index_rate) * feat + index_rate * torch.from_numpy(idx_feat).to(self.device)
                except Exception:
                    pass

            # RVC v2는 100Hz (10ms) 해상도를 기대하므로 2배 확장
            feat = feat.repeat_interleave(2, dim=0) # [T_100, 768]
            t_len = feat.shape[0]

            # 3. F0 추출 (100Hz)
            f0_arr = self.extract_f0_pm(wav, sr, f0_up_key=f0_up_key)
            
            # F0 길이 정렬
            if len(f0_arr) < t_len:
                f0_arr = np.pad(f0_arr, (0, t_len - len(f0_arr)), mode="edge")
            else:
                f0_arr = f0_arr[:t_len]

            # Coarse pitch (이산화 0~255) 및 Continuous pitch (Hz)
            coarse_pitch = f0_to_coarse(f0_arr)
            pitch_torch = torch.from_numpy(coarse_pitch).long().to(self.device).unsqueeze(0)
            pitchf_torch = torch.from_numpy(f0_arr).float().to(self.device).unsqueeze(0)

            # 4. RVC 디코더 추론
            feat_in = feat.unsqueeze(0)
            phone_lengths = torch.tensor([t_len], device=self.device)
            sid = torch.tensor([0], device=self.device)

            out_audio = self.net_g(feat_in, phone_lengths, pitch_torch, pitchf_torch, sid)
            out_np = out_audio.squeeze().cpu().numpy()

            # 음량 노멀라이징 & 저장
            max_val = np.abs(out_np).max()
            if max_val > 0.99:
                out_np = out_np / max_val * 0.98

            sf.write(str(output_wav_path), out_np, self.target_sr)
            print(f"✨ RVC 음성 변환 완료 -> {output_wav_path.name}")
            return output_wav_path
