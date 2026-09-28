from jobintel.semantic.onnx_runtime import export_fp32, export_int8

print(f"FP32: {export_fp32()}")
print(f"INT8: {export_int8()}")
