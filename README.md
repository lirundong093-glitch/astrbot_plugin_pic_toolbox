<div align="center">

[![Moe Counter](https://count.getloli.com/get/@lirundong093-glitch?theme=moebooru)](https://github.com/lirundong093-glitch/astrbot_plugin_pic_toolbox)

</div>

# 🖼️ 图片处理工具箱 (astrbot_plugin_pic_toolbox)

基于 AstrBot 框架的群聊图片处理插件，支持对静态图片和 GIF 进行反色、翻转、调速，以及生成摸头杀动画。

<p align="center">
  <img src="https://img.shields.io/badge/version-v1.0.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/AstrBot-%E6%8F%92%E4%BB%B6%E6%A1%86%E6%9E%B6-brightgreen" alt="AstrBot">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

## ✨ 功能

| 指令 | 说明 |
| :--- | :--- |
| `反色` | 对图片/GIF 执行反色处理 |
| `左右翻转` | 水平镜像翻转 |
| `上下翻转` | 垂直颠倒翻转 |
| `调速 0.3~5.0` | 调整 GIF 播放速度（如 `调速 2.0` 即两倍速） |
| `摸头` | 生成 Petpet 摸头杀 GIF（基于 [B1gM8c/Petpet](https://github.com/B1gM8c/Petpet) 算法） |

### 通用特性

- **图片来源**：引用回复图片、直接发送图片、或 `@用户` 取对方 QQ 头像（需开启 `enable_at_avatar`）
- **GIF 支持**：所有指令均正确处理 GIF 增量帧，保留时长、透明度与循环信息
- **精准匹配**：`match_mode` 开启后可直接发送词语触发，无需 `/` 前缀

## 🛠️ 配置项

| 配置 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `enable_at_avatar` | bool | true | 允许 `@用户 + 指令` 获取对方头像处理 |
| `match_mode` | bool | false | 开启后直接发「反色」即可触发，无需 `/` |

## 📦 安装与依赖

### 1. 安装依赖

```bash
pip install Pillow requests
```

### 2. 安装插件

将本插件目录放入 AstrBot 的 `addons/plugins` 对应目录，或通过 AstrBot 面板上传。

## 🖼️ 示例

<details>
<summary>点击展开效果示例</summary>

<div align="center">

### 反色
![反色](image_to_show_invert.png)

### 摸头杀
![摸头](image_to_show_petpet.gif)

</div>
</details>

## 📁 项目结构

```
astrbot_plugin_pic_toolbox/
├── main.py          # 指令路由与事件处理
├── flip.py          # 左右翻转 / 上下翻转
├── invert.py        # 反色处理
├── gif_speed.py     # GIF 调速
├── petpet.py        # 摸头杀生成器
├── gif_utils.py     # GIF 帧展开与保存公用函数
├── petpet_hand.png  # 摸头杀手部精灵图
└── _conf_schema.json
```

## 🔄 GIF 处理说明

插件使用统一的 `unfold_frames()` 将 GIF 增量帧逐帧复合为完整帧后再处理，避免非首帧局部区域导致的黑块问题。保存时自动继承原 GIF 的 `duration`、`disposal`、`loop` 和 `transparency`。

## 📝 许可证

[MIT License](LICENSE)

## 🙏 鸣谢

- [B1gM8c/Petpet](https://github.com/B1gM8c/Petpet) — 摸头杀原始算法
- [AstrBot](https://github.com/AstrBotDevs/AstrBot) — 机器人框架
- [Pillow (PIL)](https://python-pillow.org/) — 图像处理核心库

---

<p align="center">Made with ❤️ by <a href="https://github.com/lirundong093-glitch">Lucy</a></p>
