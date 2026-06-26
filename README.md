<div align="center">

[![Moe Counter](https://count.getloli.com/get/@lirundong093-glitch?theme=moebooru)](https://github.com/lirundong093-glitch/astrbot_plugin_pic_toolbox)

</div>

# 🖼️ 图片处理工具箱 (astrbot_plugin_pic_toolbox)

基于 AstrBot 框架的群聊图片 / 头像处理插件，支持静态图和 GIF 的反色、翻转、镜像对称、调速，以及摸头杀、发射、撅人、鞭笞、砍头等一系列趣味表情包生成。所有 GIF 处理统一使用增量帧展开管道，保留原图时长、透明度与循环信息。

<p align="center">
  <img src="https://img.shields.io/badge/version-v1.1.3-blue" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/AstrBot-%E6%8F%92%E4%BB%B6%E6%A1%86%E6%9E%B6-brightgreen" alt="AstrBot">
  <img src="https://img.shields.io/badge/license-AGPL--3.0-blue" alt="License">
</p>

---

## ✨ 功能一览

### 🔧 变换类

| 指令 | 说明 | 图片来源 |
| :--- | :--- | :--- |
| `反色` | 对图片 / GIF 执行反色处理 | 引用回复图片 / 直接发送图片 / `@用户`取头像 |
| `左右翻转` | 水平镜像翻转 | 同上 |
| `上下翻转` | 垂直颠倒翻转 | 同上 |
| `调速 0.3~5.0` | 调整 GIF 播放速度（如 `调速 2.0` 即两倍速）。GIF 上限 50 FPS，超限时自动回退到最接近上限的倍率并提示用户；开启 `gif_speed_allow_frame_drop` 后则通过均匀丢帧实现目标倍率 | 引用回复图片 / 直接发送图片 |

### 🔄 对称类

| 指令 | 说明 | 图片来源 |
| :--- | :--- | :--- |
| `左对称` | 保留左半边 → 镜像到右边 | 引用 / 直接 / `@用户` |
| `右对称` | 保留右半边 → 镜像到左边 | 同上 |
| `上对称` | 保留上半边 → 镜像到下边 | 同上 |
| `下对称` | 保留下半边 → 镜像到上边 | 同上 |

### 🎭 表情包 / 特效类

| 指令 | 说明 | 类型 | 图片来源 |
| :--- | :--- | :--- | :--- |
| `摸头` | 生成 Petpet 摸头杀 GIF | 单人头 | 引用 / 直接 / `@用户` |
| `发射` | 生成射击表情包（含人脸检测自动定位） | 单人头 | 引用 / 直接 / `@用户` |
| `杀` | 生成砍头表情包 GIF | 单人头 | 必须 `@用户` |
| `操你` | 生成撅人表情包（双人互动） | 双人头 | 必须 `@用户` |
| `抽你` | 生成鞭笞表情包（双人互动） | 双人头 | 必须 `@用户` |

> **双人头指令说明**：`操你` 和 `抽你` 需要同时获取指令发送者与被 @ 者的头像，因此 **必须 @一个目标用户**，否则会提示「请 @ 一个目标！」。

### 通用特性

- **图片来源**：按优先级依次尝试 ①引用回复中的图片 ②直接发送的图片 ③ `@用户` 的 QQ 头像（需开启 `enable_at_avatar`）
- **GIF 支持**：所有变换类指令均正确处理 GIF 增量帧，保留时长、透明度与循环信息
- **精准匹配**：`match_mode` 开启后可直接发送词语触发，无需 `/` 前缀
- **自动清理**：启动时清理超过 1 小时的残留临时文件，处理后 10 秒自动删除输出文件

---

## 🛠️ 配置项

| 配置 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `enable_at_avatar` | bool | `true` | 允许 `@用户 + 指令` 获取对方头像处理 |
| `match_mode` | bool | `false` | 开启后直接发「反色」即可触发，无需 `/` 前缀 |
| `gif_speed_allow_frame_drop` | bool | `false` | 调速超 50 FPS 时允许均匀丢帧实现目标倍率（默认关闭，自动回退） |

---

## ⚡ GIF 调速详解

`调速` 指令支持 0.3× ~ 5.0× 变速。GIF 调速遵循 **最高 50 FPS** 的硬上限（对应每帧最短 20ms），超出上限时有两种策略：

### 默认策略：自动取最接近上限倍率（推荐）

当请求倍率导致帧率超过 50 FPS 时，插件会自动计算一个 **不超过 50 FPS 的最高合法倍率**（保留一位小数），并回退到该倍率执行。

> 例如：原 GIF 为 30 FPS，请求 ×2.0 → 目标 60 FPS 超出上限，自动回退至 ×1.6 → 约 48 FPS，并提示用户实际使用的倍率。

### 丢帧模式：`gif_speed_allow_frame_drop`

开启此配置后，调速不再回退倍率，而是通过 **均匀丢帧** 保证每帧间隔不低于 20ms，从而在遵守 50 FPS 上限的同时实现目标倍率。

> 例如：30 帧 GIF，请求 ×5.0，插件计算需要保留的帧数后每隔若干帧取一帧，确保最终帧率在 50 FPS 以内并提示丢帧信息。

| 策略 | 效果 | 流畅度 | 适用场景 |
| :--- | :--- | :--- | :--- |
| 自动回退（默认） | 保留全部帧，倍率自动下调 | 流畅 | 日常调速 |
| 允许丢帧 | 达到目标倍率，帧数减少 | 有跳帧感 | 追求极致加速 |

---

## 📦 安装与依赖

### 1. 安装插件

将本插件目录放入 AstrBot 的插件目录，或通过 AstrBot 管理面板上传安装。

```bash
# 方式一：软链接
ln -s /path/to/astrbot_plugin_pic_toolbox /path/to/astrbot/addons/plugins/

# 方式二：直接放入
cp -r astrbot_plugin_pic_toolbox /path/to/astrbot/addons/plugins/
```

### 2. 安装依赖

```bash
pip install Pillow>=10.0.0 requests>=2.25.0
```

**可选依赖**（`发射` 指令需要人脸检测功能）：

```bash
# 二选一
pip install opencv-python      # GUI 完整版
pip install opencv-python-headless  # 无头版（推荐服务器使用）

# opencv-python 会自动安装 numpy，无需单独安装
```

> 如果不安装 opencv-python，`发射` 指令将不可用，其他功能不受影响。

---

## 🖼️ 使用示例

### 基础变换

```
用户：（发送一张图片）
用户：反色
Bot：  [返回反色后的图片]

用户：（引用一条含 GIF 的消息）
用户：/调速 2.0
Bot：  [返回 2 倍速的 GIF]
```

### @用户取头像

```
用户：@某人 左对称
Bot：  [获取该用户头像 → 左对称处理后返回]
```

### 双人头表情包

```
用户：@某人 操你
Bot：  [取发送者 + 被 @ 者头像 → 生成撅人 GIF]

用户：@某人 抽你
Bot：  [取发送者 + 被 @ 者头像 → 生成鞭笞 GIF]
```

---

## 📁 项目结构

```
astrbot_plugin_pic_toolbox/
├── main.py              # 插件主体：指令路由与事件处理
├── metadata.yaml        # 插件元数据
├── _conf_schema.json    # 配置 Schema
├── requirements.txt     # Python 依赖
├── logo.png             # 插件图标
├── meme/                # 图像处理模块
│   ├── __init__.py
│   ├── gif_utils.py     # GIF 帧展开与保存公用函数
│   ├── invert.py        # 反色处理
│   ├── flip.py          # 水平 / 垂直翻转
│   ├── mirror.py        # 左 / 右 / 上 / 下对称
│   ├── gif_speed.py     # GIF 调速
│   ├── petpet.py        # 摸头杀生成器
│   ├── shoot.py         # 射击表情包（含人脸检测）
│   ├── do.py            # 撅人表情包（双人头）
│   ├── lash.py          # 鞭笞表情包（双人头）
│   └── behead.py        # 砍头表情包（单人头）
└── resource/            # 资源素材
    ├── petpet_hand.png  # 摸头杀手部精灵图
    ├── do_frames/       # 撅人底图帧（3 帧）
    ├── shoot_frames/    # 射击底图帧（13 帧）
    ├── lash_frames/     # 鞭笞底图帧（9 帧）
    └── behead_frames/   # 砍头底图帧（21 帧）
```

---

## 🔄 GIF 处理说明

插件使用统一的 `unfold_frames()` 将 GIF 增量帧逐帧复合为完整帧后再处理，避免非首帧局部区域导致的黑块问题。保存时自动继承原 GIF 的：

- `duration`（每帧时长）
- `disposal`（帧处置方式）
- `loop`（循环次数）
- `transparency`（透明索引）

---

## 📝 许可证

[GNU AGPL v3.0 License](LICENSE)

---

## 🙏 鸣谢

- [B1gM8c/Petpet](https://github.com/B1gM8c/Petpet) — 摸头杀原始算法
- [meme-generator](https://github.com/MeetWq/meme-generator) — 发射 / 撅人 / 鞭笞 / 砍头表情包灵感来源
- [AstrBot](https://github.com/AstrBotDevs/AstrBot) — 机器人框架
- [Pillow (PIL)](https://python-pillow.org/) — 图像处理核心库
- [OpenCV](https://opencv.org/) — 人脸检测（`发射` 指令）

---

<p align="center">Made with ❤️ by <a href="https://github.com/lirundong093-glitch">Lucy</a></p>
