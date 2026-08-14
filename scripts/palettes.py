# -*- coding: utf-8 -*-
"""Built-in categorical color palettes for academic figures.

This module only contains palette data; see ``palette_manager.py`` for the
query / extension / preview API.

All palettes are qualitative (categorical). They are NOT continuous colormaps
and should not be used as such by default.
"""

PALETTES = {
    "pastel_girl": {
        "id": "pastel_girl",
        "name_zh": "粉彩少女",
        "tags": ["pastel", "soft", "pink", "purple", "low-saturation"],
        "colors": [
            "#B6B3D6",
            "#CFCCE3",
            "#D5D3DE",
            "#D5D1D1",
            "#F6DFD6",
            "#F8B2A2",
            "#F1837A",
            "#E9687A",
        ],
        "type": "categorical",
        "source": "custom",
    },
    "sweet_macaron": {
        "id": "sweet_macaron",
        "name_zh": "甜蜜马卡龙",
        "tags": ["macaron", "pastel", "bright", "cute"],
        "colors": [
            "#F7A6AC",
            "#F7B2C7",
            "#F3BBB1",
            "#EEC78A",
            "#EEE9A2",
            "#CBE4B1",
            "#B3DDCB",
            "#B8E5FA",
        ],
        "type": "categorical",
        "source": "custom",
    },
    "soft_forest": {
        "id": "soft_forest",
        "name_zh": "柔绿森林",
        "tags": ["forest", "nature", "green", "muted"],
        "colors": [
            "#B8DBB3",
            "#86BC79",
            "#71A682",
            "#81989B",
            "#D19246",
            "#B5AF8B",
            "#7EA4B6",
            "#4A4F7E",
        ],
        "type": "categorical",
        "source": "custom",
    },
    "blue_green_land": {
        "id": "blue_green_land",
        "name_zh": "蓝天绿地",
        "tags": ["blue", "green", "nature", "contrast"],
        "colors": [
            "#377EB8",
            "#B23648",
            "#DC7369",
            "#D8EBCD",
            "#F8EFB5",
            "#DAD4B9",
            "#C8CDCF",
            "#E1F3FA",
        ],
        "type": "categorical",
        "source": "custom",
    },
    "watercolor_bloom": {
        "id": "watercolor_bloom",
        "name_zh": "水色花影",
        "tags": ["watercolor", "teal", "purple", "floral"],
        "colors": [
            "#3AB5B3",
            "#7B6C9F",
            "#A188BD",
            "#BBC5DE",
            "#E7777F",
            "#976793",
            "#61829D",
            "#80C66D",
        ],
        "type": "categorical",
        "source": "custom",
    },
    "fresh_holiday": {
        "id": "fresh_holiday",
        "name_zh": "清新假日",
        "tags": ["fresh", "holiday", "green", "blue", "orange"],
        "colors": [
            "#6AD1A3",
            "#7FBDDA",
            "#BBC7BE",
            "#FFD47D",
            "#FFA288",
            "#C49892",
            "#929EAB",
            "#84ADDC",
        ],
        "type": "categorical",
        "source": "custom",
    },
    "summer_beach": {
        "id": "summer_beach",
        "name_zh": "夏日海滩",
        "tags": ["summer", "beach", "coral", "orange", "blue"],
        "colors": [
            "#FC757B",
            "#F97F5F",
            "#FAA26F",
            "#FDCD94",
            "#FEE199",
            "#B0D6A9",
            "#65BDBA",
            "#3C9BC9",
        ],
        "type": "categorical",
        "source": "custom",
    },
}


# Chinese-name aliases -> canonical palette id.
ZH_TO_ID = {
    info["name_zh"]: pid
    for pid, info in PALETTES.items()
}
