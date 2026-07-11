# PptxGenJS 构建指南

本技能锁定 PptxGenJS 4.x 接口。执行 `npm install` 安装 `pptxgenjs`、`sharp`、`react`、`react-dom`、`react-icons` 与 TypeScript 运行器 `tsx`。

```powershell
node --version
npm --version
npm install
npm exec tsx scripts/init-deck.ts -- --help
```

依赖安装失败时报告 npm 错误和代理/证书状态，不复制外部 `node_modules`。

- 页面比例使用 `LAYOUT_WIDE`。
- 作者、公司、主题、标题和语言由简报提供。
- 主题令牌集中在 `theme.ts`。
- 页面代码通过 `components.ts` 登记几何框。
- 生成后必须由真实 Office 后端渲染，不以“写出文件”代替验收。

