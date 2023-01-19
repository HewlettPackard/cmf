# Please change the dataset directory to your actual directory
data_root = '/lustre/data/hdcdatasets/'

# dataset settings
dataset_type = 'HDCDataset'
img_norm_cfg = dict(
    mean=[123.675, 123.675, 123.675], std=[58.395, 58.395, 58.395], to_rgb=True)
train_pipeline = [
    #dict(type='LoadImageFromFile', color_type='grayscale'),
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations', with_bbox=True),
    dict(type='Resize', img_scale=(1000, 600), keep_ratio=True),
    dict(type='RandomFlip', flip_ratio=0.5),
    dict(type='Normalize', **img_norm_cfg),
    dict(type='Pad', size_divisor=32),
    dict(type='DefaultFormatBundle'),
    dict(type='Collect', keys=['img', 'gt_bboxes', 'gt_labels']),
]
test_pipeline = [

    #dict(type='LoadImageFromFile', color_type='grayscale'),
    dict(type='LoadImageFromFile'),
    dict(
        type='MultiScaleFlipAug',
        img_scale=(1000, 600),
        flip=False,
        transforms=[
            dict(type='Resize', keep_ratio=True),
            dict(type='RandomFlip'),
            dict(type='Normalize', **img_norm_cfg),
            dict(type='Pad', size_divisor=32),
            dict(type='ImageToTensor', keys=['img']),
            dict(type='Collect', keys=['img']),
        ])
]
data = dict(
    samples_per_gpu=2,
    workers_per_gpu=2,
    train=dict(
        type='RepeatDataset',
        times=3,
        dataset=dict(
            type=dataset_type,
            ann_file=[
                data_root + 'hdc/ImageSets/Main/trainval.txt'
            ],
            img_prefix=[data_root + 'hdc/'],
            pipeline=train_pipeline)),
    val=dict(
        type=dataset_type,
        ann_file=data_root + 'hdc/ImageSets/Main/test.txt',
        img_prefix=data_root + 'hdc/',
        pipeline=test_pipeline),
    test=dict(
        type=dataset_type,
        ann_file=data_root + 'hdc/ImageSets/Main/test.txt',
        img_prefix=data_root + 'hdc/',
        pipeline=test_pipeline))
evaluation = dict(interval=1, metric='mAP')
