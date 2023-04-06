checkpoint_config = dict(interval=1)
# yapf:disable
log_config = dict(
    pipeline="active_learning",
    stage="Train",
    execution="Train",
    interval=1,
    hooks=[
        dict(type='TextLoggerHook'),
        dict(type='TensorboardLoggerHook'),
        dict(type='CMFLoggerHook')
    ])
# yapf:enable
dist_params = dict(backend='nccl')
log_level = 'INFO'
load_from = None
resume_from = None
workflow = [('train', 1)]
