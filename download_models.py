from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='myshell-ai/OpenVoice',
    local_dir='checkpoints_v2',
    repo_type='model'
)
print('Done')