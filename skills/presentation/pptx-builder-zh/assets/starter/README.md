# PPTX Builder 起步方式

1. 复制 `slide-spec.json` 与可选 `theme.json` 到项目输出目录。
2. 在本 Skill 根目录执行 `npm install`。
3. 调用 `scripts/init-deck.ts`，把 `--output` 和 `--manifest` 指向项目输出目录。
4. 调用 `scripts/check-bounds.ts`。
5. 切换到 `ppt-render-qa-zh` 完成真实渲染和修复复验。

不要复制 `node_modules` 到交付包；交付 `package.json` 与锁文件即可。

