# 闪电剑资源包模板

改贴图/改姿势**不用重新编译模组**，用这个资源包盖上去就行。

## 用法

1. 把整个 `resourcepack-template` 文件夹复制到：
   - 正式游戏：`.minecraft/resourcepacks/`（可以随便改个名字，比如 `我的闪电剑`）
   - 开发环境：`run/resourcepacks/`
2. 游戏里 **选项 → 资源包** 启用它，放在模组资源之上（默认就在上面）。
3. 改完文件按 **`F3+T`** 重载，立刻生效，不用重启。

## 文件对应关系

### 贴图

```
assets/lightning_sword/textures/item/lightning_sword.png
```

- **静态**：16×16 PNG，背景透明，剑刃从左下的护手指向右上的剑尖。
- **动画**：16×(16×N) PNG，N 帧**竖着**排；同时放一个同名的
  `lightning_sword.png.mcmeta`：

  ```json
  { "animation": { "frametime": 2, "interpolate": false } }
  ```

  `frametime` = 每帧停留的游戏刻数（2 ≈ 每秒 10 帧），调小闪得更快；
  模板里给的是 8 帧。

  矿物的贴图在 `textures/block/lightning_ore.png`（16×16，静态）。

### 模型 / 手持角度

```
assets/lightning_sword/models/item/lightning_sword.json          <- 基模，带 8 个 overrides
assets/lightning_sword/models/item/lightning_sword_aim_0..7.json <- 8 套蓄力姿势
```

想改**蓄力时剑的握持角度**，就在资源包里放同名的
`lightning_sword_aim_N.json`，改它的 `display` 块：

```json
{
  "parent": "minecraft:item/handheld",
  "textures": { "layer0": "lightning_sword:item/lightning_sword" },
  "display": {
    "firstperson_righthand": {
      "rotation": [ 60, -90, 25 ],
      "translation": [ 1.13, 3.2, 1.13 ],
      "scale": [ 0.78, 0.78, 0.78 ]
    },
    "thirdperson_righthand": {
      "rotation": [ 60, -90, 55 ],
      "translation": [ 0, 4.0, 0.5 ],
      "scale": [ 0.85, 0.85, 0.85 ]
    }
  }
}
```

`rotation` 是 `[X, Y, Z]` 度，`translation` 单位是 1/16 格。

### 换成自己的 3D 模型

用 Blockbench 导出成 Java 方块/物品模型 JSON，放进
`assets/lightning_sword/models/item/`，然后把 `lightning_sword.json` 的 `parent`
改成那个模型；只要模型里引用的贴图名写成
`lightning_sword:item/你的贴图`，就能直接换掉整把剑的外观。

> 注意：`lightning_sword.json` 里的 `overrides` 是 8 套姿势的选择器，用自己模型的话
> 记得保留 `overrides` 那一段（或者把 `lightning_sword_aim_*` 也一起替换）。
