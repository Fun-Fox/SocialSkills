# 抖音养号技能 - Douyin Nurturing

## 技能名称
DouyinNurturingSkill - 抖音养号助手

## 技能描述
自动化抖音账号养号操作，使用 uiautomator2 实现抖音账号的自动化养号，包括：
- 自动浏览推荐视频
- 随机点赞（可配置概率）
- 随机关注（可配置概率）
- 随机搜索关键词并浏览搜索结果
- 完整的统计信息输出

**版本**: 3.0 (简化版)

---

## 输入判断

按以下顺序判断用户意图：

1. **用户要求"启动/运行/执行养号"**: 直接进入养号执行流程
2. **用户已提供完整参数**: 确认参数后直接执行
3. **用户提供部分参数**: 先补齐缺失信息（主要是 deviceName），等待用户确认
4. **信息不全**: 先询问缺失的必要参数（设备名称），不要直接执行

---

## 必做约束

- ✅ **执行前必须让用户确认最终参数**（设备名、端口等）
- ✅ **环境已配置完成**，无需额外检查或安装
- ✅ **运行时间不超过 60 分钟**；若用户要求更长时间，需分批次执行或提醒风险
- ✅ **如使用文件路径，优先使用绝对路径**
- ✅ **如执行失败**，优先检查元素定位器、设备连接状态
- ✅ **养号过程中必须记录关键指标**（浏览数、点赞数、关注数、搜索次数）
- ✅ **Python 环境和 uiautomator2 已手动安装完成**

---

## 环境说明

### 部署结构

```
~/.zeroclaw/workspace/skills/
└── SocialSkills/                  # 技能根目录
    ├── scripts/
    │   └── douyin_nurturing.py    # 养号脚本
    ├── SKILL.md                   # 本技能文档
    ├── README.md                  # 项目说明
    └── requirements.txt           # Python 依赖
```

### 所需工具（已手动安装）

- ✅ **ADB** - 系统已安装
- ✅ **Python 3.x** - 系统 Python
- ✅ **uiautomator2** - 已手动安装

---

## 使用说明

### 快速开始（两步）

```bash
# 1. 连接设备（WiFi 方式，端口 5555）
adb connect 192.168.1.100:5555

# 2. 运行养号任务
python3 scripts/douyin_nurturing.py -d 192.168.1.100:5555 --seconds 600
```

### 完整流程

```bash
# 1. 连接设备
adb connect 192.168.1.100:5555

# 2. 验证连接
adb devices
# 应该看到：192.168.1.100:5555    device

# 3. 执行养号任务
python3 scripts/douyin_nurturing.py -d 192.168.1.100:5555 --seconds 600

# 4. 断开设备（可选）
adb disconnect 192.168.1.100:5555
```

---

## 参数说明

### 必填参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `-d` / `--deviceName` | 设备名称（WiFi IP:端口） | `192.168.1.100:5555` |

### 常用可选参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--seconds` | 运行秒数 | `600` (10 分钟) | `--seconds 1800` |
| `--like_prob` | 点赞概率 (%) | `10` | `--like_prob 20` |
| `--collect_prob` | 关注概率 (%) | `10` | `--collect_prob 15` |
| `--searchProb` | 搜索概率 (%) | `80` | `--searchProb 50` |
| `--keyWord` | 搜索关键词 | `美食\n游戏\n娱乐` | `--keyWord "美食\n旅游"` |

### 其他可选参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-a` / `--adbPort` | ADB 端口 | `5037` |
| `-accountId` | 目标账号 ID | `"000"` |
| `-job_id` | 任务 ID | `None` |
| `-ver` / `--platformVersion` | 平台版本 | `None` |
| `-v` / `--variables` | 目标变量 | `'{}'` |

---

## 使用示例

### 示例 1：基础用法（运行 10 分钟）

```bash
python3 scripts/douyin_nurturing.py -d 192.168.1.100:5555
```

### 示例 2：自定义运行时长和概率

```bash
python3 scripts/douyin_nurturing.py -d 192.168.1.100:5555 \\
    --seconds 1800 \\
    --like_prob 20 \\
    --collect_prob 15
```

### 示例 3：自定义搜索关键词

```bash
python3 scripts/douyin_nurturing.py -d 192.168.1.100:5555 \\
    --keyWord "美食\\n旅游\\n健身"
```

### 示例 4：完整参数

```bash
python3 scripts/douyin_nurturing.py -d 192.168.1.100:5555 \\
    --seconds 1800 \\
    --like_prob 20 \\
    --collect_prob 10 \\
    --searchProb 80 \\
    --keyWord "美食\\n游戏\\n娱乐"
```

---

## 运行日志示例

```log
2026-03-17 10:00:00 - douyin_nurturing.py[line:244] - INFO: 开始执行抖音养号任务
2026-03-17 10:00:02 - douyin_nurturing.py[line:236] - INFO: 设备 192.168.1.100:5555 连接成功
2026-03-17 10:00:04 - douyin_nurturing.py[line:259] - INFO: 启动抖音应用...
2026-03-17 10:00:12 - douyin_nurturing.py[line:262] - INFO: 抖音应用已启动
2026-03-17 10:00:15 - douyin_nurturing.py[line:329] - INFO: 正在浏览第 1 个视频
2026-03-17 10:00:26 - douyin_nurturing.py[line:528] - INFO: 点赞成功 (双击屏幕)
2026-03-17 10:01:35 - douyin_nurturing.py[line:415] - INFO: 正在搜索：美食
2026-03-17 10:10:00 - douyin_nurturing.py[line:589] - INFO: 养号任务完成

==================================================
养号任务统计:
  浏览视频总数：45
  点赞数量：8
  关注数量：3
  搜索次数：12
==================================================
```

---

## 关键指标统计

执行完成后会输出以下统计信息：

- **浏览视频总数** (`view_count`)
- **点赞数量** (`like_count`)
- **关注数量** (`follow_count`)
- **评论数量** (`comment_count`)
- **搜索次数** (`search_operations`)
- **运行时长** (`duration`)

---

## 失败处理

| 问题 | 解决方案 |
|------|----------|
| **连接失败** | 检查设备是否连接、USB 调试是否开启 |
| **设备未授权** | 在设备上点击"允许 USB 调试" |
| **元素定位失败** | 抖音版本可能已更新，需检查元素定位器 |
| **应用启动失败** | 检查抖音是否已安装在设备上 |
| **ADB 命令失败** | 确认 ADB 已预装且可用 |
| **运行超时** | 建议分批次执行，或增加 `--seconds` 参数 |
| **UiAutomation 冲突** | 脚本会自动清理，也可手动运行清理脚本 |

---

## 注意事项

1. ✅ **环境已配置完成** - Python 和 uiautomator2 已手动安装
2. ✅ **设备必须保持屏幕常亮** - 建议关闭自动锁屏
3. ✅ **确保网络稳定** - WiFi 或移动数据均可
4. ✅ **抖音版本必须为最新版** - 旧版本可能元素 ID 不同
5. ✅ **养号过程中不要手动操作设备** - 会干扰自动化流程
6. ✅ **建议每次养号不超过 30 分钟** - 避免被识别为异常行为
7. ✅ **点赞、关注、搜索概率应根据实际需求调整** - 避免过于频繁
8. ✅ **运行时间不宜超过 60 分钟** - 如需更长，请分批次执行
9. ✅ **首次运行建议使用默认参数** - 熟悉流程后再调整
10. ✅ **必须使用 WiFi 连接设备** - TCP 端口固定使用 5555

---

## 常见问题

### Q1: 如何查看设备 IP？

**A**: 在设备的 WiFi 设置中查看当前连接网络的 IP 地址。

### Q2: 连接失败怎么办？

**A**: 
1. 确认设备和电脑在同一局域网
2. 确认设备已开启开发者选项和 USB 调试
3. 尝试重新连接：`adb disconnect` 然后 `adb connect IP:5555`

### Q3: 如何停止正在运行的脚本？

**A**: 按 `Ctrl+C` 即可，脚本会自动清理服务并退出。

### Q4: UiAutomation 冲突如何解决？

**A**: 脚本已集成自动清理功能，如果仍然遇到冲突，可以手动清理：

```bash
adb -s 192.168.1.100:5555 shell am force-stop com.github.uiautomator
adb -s 192.168.1.100:5555 shell am force-stop com.wetest.uia2
```

---

## 参考资料

- [uiautomator2 官方文档](https://github.com/openatx/uiautomator2)
- [元素定位方法](https://github.com/openatx/uiautomator2#writer-document)
- [ADB 使用指南](https://developer.android.com/studio/command-line/adb)

---

**最后更新**: 2026-03-17  
