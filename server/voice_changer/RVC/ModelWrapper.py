import onnxruntime
import torch
import numpy as np
import json

# providers = ['OpenVINOExecutionProvider', "CUDAExecutionProvider", "DmlExecutionProvider", "CPUExecutionProvider"]
providers = ["CUDAExecutionProvider"]


class ModelWrapper:
    def __init__(self, onnx_model):
        self.onnx_model = onnx_model

        # ort_options = onnxruntime.SessionOptions()
        # ort_options.intra_op_num_threads = 8
        self.onnx_session = onnxruntime.InferenceSession(
            self.onnx_model, providers=providers
        )
        # input_info = s
        first_input_type = self.onnx_session.get_inputs()[0].type
        if first_input_type == "tensor(float)":
            self.is_half = False
        else:
            self.is_half = True
        modelmeta = self.onnx_session.get_modelmeta()
        try:
            metadata = json.loads(modelmeta.custom_metadata_map["metadata"])
            self.samplingRate = metadata["samplingRate"]
            self.f0 = metadata["f0"]
            self.embChannels = metadata["embChannels"]
            self.modelType = metadata["modelType"]
            self.deprecated = False
            self.embedder = (
                metadata["embedder"] if "embedder" in metadata else "hubert_base"
            )
            print(
                f"[Voice Changer] Onnx metadata: sr:{self.samplingRate}, f0:{self.f0}, embedder:{self.embedder}"
            )
        except:
            self.samplingRate = 48000
            self.f0 = True
            self.embChannels = 256
            self.modelType = 0
            self.deprecated = True
            self.embedder = "hubert_base"
            print(
                "[Voice Changer] ############## !!!! CAUTION !!!! ####################"
            )
            print(
                "[Voice Changer] This onnx's version is depricated. Please regenerate onnxfile. Fallback to default"
            )
            print(
                f"[Voice Changer] Onnx metadata: sr:{self.samplingRate}, f0:{self.f0}"
            )
            print(
                "[Voice Changer] ############## !!!! CAUTION !!!! ####################"
            )

    def getSamplingRate(self):
        return self.samplingRate

    def getF0(self):
        return self.f0

    def getEmbChannels(self):
        return self.embChannels

    def getModelType(self):
        return self.modelType

    def getDeprecated(self):
        return self.deprecated

    def getEmbedder(self):
        return self.embedder

    def set_providers(self, providers, provider_options=[{}]):
        self.onnx_session.set_providers(
            providers=providers, provider_options=provider_options
        )

    def get_providers(self):
        return self.onnx_session.get_providers()

    def infer_pitchless(self, feats, p_len, sid):
        if self.is_half:
            audio1 = self.onnx_session.run(
                ["audio"],
                {
                    "feats": feats.cpu().numpy().astype(np.float16),
                    "p_len": p_len.cpu().numpy().astype(np.int64),
                    "sid": sid.cpu().numpy().astype(np.int64),
                },
            )
        else:
            audio1 = self.onnx_session.run(
                ["audio"],
                {
                    "feats": feats.cpu().numpy().astype(np.float32),
                    "p_len": p_len.cpu().numpy().astype(np.int64),
                    "sid": sid.cpu().numpy().astype(np.int64),
                },
            )
        return torch.tensor(np.array(audio1))

    def infer(self, feats, p_len, pitch, pitchf, sid):
        if self.is_half:
            audio1 = self.onnx_session.run(
                ["audio"],
                {
                    "feats": feats.cpu().numpy().astype(np.float16),
                    "p_len": p_len.cpu().numpy().astype(np.int64),
                    "pitch": pitch.cpu().numpy().astype(np.int64),
                    "pitchf": pitchf.cpu().numpy().astype(np.float32),
                    "sid": sid.cpu().numpy().astype(np.int64),
                },
            )
        else:
            audio1 = self.onnx_session.run(
                ["audio"],
                {
                    "feats": feats.cpu().numpy().astype(np.float32),
                    "p_len": p_len.cpu().numpy().astype(np.int64),
                    "pitch": pitch.cpu().numpy().astype(np.int64),
                    "pitchf": pitchf.cpu().numpy().astype(np.float32),
                    "sid": sid.cpu().numpy().astype(np.int64),
                },
            )

        return torch.tensor(np.array(audio1))
