# Please change the dataset directory to your actual directory
#data_root = '/lustre/data/hdcdatasets/'
data_root = '/mnt/beegfs/HDC/data/tomography_data/tiled_annotations/'

# dataset settings
dataset_type = 'HDCDataset'
img_norm_cfg = dict(
    mean=[123.675, 123.675, 123.675], std=[58.395, 58.395, 58.395], to_rgb=True)
train_pipeline = [
    #dict(type='LoadImageFromFile', color_type='grayscale'),
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations', with_bbox=True),
    dict(type='Resize', img_scale=(960, 960), keep_ratio=True),
    dict(type='RandomFlip', flip_ratio=0.5),#,direction=['horizontal','vertical','diagonal']),
    dict(type='RandomFlip', flip_ratio=0.5,direction='vertical'),

    dict(type='Normalize', **img_norm_cfg),
    dict(type='Pad', size_divisor=32),
    '''dict(type='Albu',
    transforms=[dict(
        type='ShiftScaleRotate',
        shift_limit=0.0,
        scale_limit=0.0,
        rotate_limit=[90,90],
        interpolation=1,
        p=0.5),
        ],
    bbox_params=dict(
            type='BboxParams',
            format='pascal_voc',
            label_fields=['gt_labels'],
            min_visibility=0.0,
            filter_lost_elements=True),
    keymap={
            'img': 'image',
            'gt_masks': 'masks',
            'gt_bboxes': 'bboxes'
        },
    update_pad_shape=False,
    skip_img_without_anno=False
    ),'''
    dict(type='DefaultFormatBundle'),
    dict(type='Collect', keys=['img', 'gt_bboxes', 'gt_labels']),
]
test_pipeline = [

    #dict(type='LoadImageFromFile', color_type='grayscale'),
    dict(type='LoadImageFromFile'),
    dict(
        type='MultiScaleFlipAug',
        img_scale=(960, 960),
        flip=False,
        transforms=[
            dict(type='Resize', keep_ratio=True),
            dict(type='RandomFlip', flip_ratio=0.5),#,direction=['horizontal','vertical','diagonal']),
            dict(type='RandomFlip', flip_ratio=0.5,direction='vertical'),
            dict(type='Normalize', **img_norm_cfg),
            dict(type='Pad', size_divisor=32),
            dict(type='ImageToTensor', keys=['img']),
            dict(type='Collect', keys=['img']),
        ])
]
data = dict(
    samples_per_gpu=8,
    workers_per_gpu=8,
    train=dict(
        type='RepeatDataset',
        times=3,#was 3
        dataset=dict(
            type=dataset_type,
            ann_file=[
                data_root + 'train.txt'#training set indexes
            ],
            img_prefix=[data_root ],
            pipeline=train_pipeline)),
    val=dict(
        type=dataset_type,
        ann_file=data_root + 'train_val.txt',#test set indexes
        img_prefix=data_root,
        pipeline=test_pipeline),
    test=dict(
        type=dataset_type,
        ann_file=data_root + 'train.txt',#should be same as training
        img_prefix=data_root ,
        pipeline=test_pipeline))
evaluation = dict(interval=1, metric='mAP')
