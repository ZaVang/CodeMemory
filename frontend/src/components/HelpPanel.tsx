interface Props {
  onClose: () => void
}

const CLI_COMMANDS = [
  {
    cmd: 'overview',
    args: '[--tags <t>] [--format inject] [--with-recall]',
    desc: '扫视：列出记忆摘要，可按 tag 过滤。会话启动时自动注入 top 5。',
    layer: 'Layer 0 认知接口',
  },
  {
    cmd: 'focus',
    args: '<id> --level full|summary [--content "..."] [--resolve]',
    desc: '注视：动态切换特定记忆的分辨率。full = 加载正文，summary = 仅摘要。',
    layer: 'Layer 0 认知接口',
  },
  {
    cmd: 'resolve',
    args: '<id> [--depth required|recommended|full] [--budget N] [--focus decision]',
    desc: '重构：从入口 atom 出发沿 imports 递归，拓扑排序输出完整因果上下文。此操作触发 maturity 自动升级。',
    layer: 'Layer 0 认知接口',
  },
  {
    cmd: 'snapshot',
    args: '<id> [--target <id> | --from-dag <json_file>]',
    desc: '残留持久化：将瞬态推理链固化到 user/snapshots/，下次可复现完整上下文。',
    layer: 'Layer 0 认知接口',
  },
  {
    cmd: 'wander',
    args: '[--mode cool|random] [--inject]',
    desc: '触景生情：随机或加权激活冷记忆（低 access_count + 高 intensity）。',
    layer: 'Layer 0 认知接口',
  },
  {
    cmd: 'create',
    args: '--id <id> [--intensity N] [--tags "a,b"] [--schema <id>] [--dry-run]',
    desc: '创建新记忆（atom），生成 .md 文件 + frontmatter 模板。',
    layer: 'CRUD',
  },
  {
    cmd: 'update',
    args: '<id> --change-note "..." [--body "..."] [--summary "..."] [--status archived]',
    desc: '更新记忆：修改 body/summary/tags/intensity，自动递增版本号 + 追加 change_log。',
    layer: 'CRUD',
  },
  {
    cmd: 'reindex',
    args: '',
    desc: '重建索引：扫描所有 .md 文件 → 解析 frontmatter → 写入 index.json。',
    layer: '维护',
  },
  {
    cmd: 'validate',
    args: '[-v|-q]',
    desc: '验证：循环依赖检测 + 断链引用 + schema 合规 + maturity 复核建议。',
    layer: '维护',
  },
  {
    cmd: 'search',
    args: '[--query <q>] [--tags <t>] [--type <t>] [--status <s>] [--maturity proven] [--semantic-type decision] [--has-imports] [--has-schema]',
    desc: '检索：多维度过滤记忆列表，支持全文 + tag + 类型 + 成熟度组合查询。',
    layer: '检索',
  },
  {
    cmd: 'orphans',
    args: '[--type <t>] [--min-intensity <n>]',
    desc: '孤立发现：找到入度为 0 的记忆（不被任何其他记忆引用）。',
    layer: '分析',
  },
  {
    cmd: 'changelog',
    args: '<id>',
    desc: '变更历史：查看指定记忆的完整版本变更记录。',
    layer: '分析',
  },
  {
    cmd: 'log',
    args: '[--limit N]',
    desc: '审计日志：全局追加日志，记录 create/update/snapshot/maturity 升级等所有事件。',
    layer: '审计',
  },
  {
    cmd: 'import',
    args: '--file <notes.txt> --extract preferences | --stdin --extract decisions',
    desc: '冷启动导入：从文本中提取并生成 draft maturity 的原子记忆。',
    layer: '导入',
  },
  {
    cmd: 'suggest-deps',
    args: '<id> [--min-score N] [--forward-only] [--retroactive-only]',
    desc: '依赖推断：三层过滤（tag_overlap×3 + schema_pattern×5 + dependents），双向推断。',
    layer: '分析',
  },
]

const UI_GUIDE = [
  {
    section: 'Graph 视图',
    items: [
      { name: 'DAG 依赖图', desc: '展示所有记忆节点及其 imports 关系。节点颜色按目录区分，大小按 intensity，边框颜色标识所属目录。边样式：实线=required，虚线=recommended，点线=related。' },
      { name: '点击节点', desc: '右侧滑出详情面板，展示 frontmatter 元数据 + markdown 正文。' },
      { name: '右键节点', desc: '弹出菜单：View Details（查看详情）/ Edit（编辑记忆）。' },
      { name: '拖拽/滚轮', desc: '拖拽平移画布，滚轮缩放。' },
    ],
  },
  {
    section: '工具栏',
    items: [
      { name: 'Search 搜索', desc: '按 tag、目录、maturity 或关键词过滤。匹配节点金色高亮，非匹配节点淡化。' },
      { name: 'Budget 滑块', desc: 'Token 预算控制器（200–5000）。拖动时实时重新 resolve，被裁剪的节点会变半透明 + 缩小 + 虚线边框。' },
      { name: 'Dagre', desc: '分层布局，自上而下展示依赖关系方向。这是当前唯一的图布局方式。' },
      { name: 'Create Memory', desc: '创建新记忆表单。填写 id、summary、tags、intensity、body 后提交。' },
      { name: '快捷键', desc: '1=Graph / 2=List / 3=Dashboard / Ctrl+K=Search / Ctrl+N=Create / Ctrl+Z=Undo / ?=Shortcuts / Esc=Close' },
    ],
  },
  {
    section: '详情面板（滑出窗）',
    items: [
      { name: '元数据卡片', desc: '展示 status / maturity 徽章、type、id、tags、intensity、version、created/updated 时间、imports 依赖列表。' },
      { name: 'Resolve 按钮', desc: '以当前记忆为入口，运行 DAG 拓扑解析。图上的节点按拓扑顺序依次金色高亮（300ms/步），展示依赖加载顺序。' },
      { name: 'Markdown 正文', desc: '完整渲染的记忆 body 内容，支持标题、列表、表格、代码块等 GFM 语法。' },
      { name: '关闭方式', desc: '点击 ✕ 按钮 / 点击遮罩层 / 按 Escape 键。' },
    ],
  },
  {
    section: 'Dashboard 视图',
    items: [
      { name: '统计卡片', desc: '总记忆数、stale 数量、proven 数量、draft 数量一目了然。' },
      { name: 'Maturity 分布', desc: '横向柱状图展示 draft / verified / proven 各有多少条。' },
      { name: 'Top Tags', desc: '按频次排序的 tag 列表，了解记忆体系的知识领域分布。' },
      { name: 'Stale 列表', desc: '高亮展示所有正文与摘要不同步的 stale 记忆，点击可跳转到 Graph 视图查看。' },
      { name: 'Wander 按钮', desc: '随机召回一条冷记忆（低访问 + 高重要度加权），弹窗展示其 summary。' },
      { name: 'Validate 按钮', desc: '运行系统诊断，展示 errors（红色）和 warnings（琥珀色）。' },
    ],
  },
  {
    section: 'Legend 图例',
    items: [
      { name: '目录颜色', desc: '从实际数据集中动态派生。节点边框颜色反映其所属目录。预定义调色板覆盖常见目录，未知目录自动分配回退颜色（标注 auto）。' },
      { name: '边类型', desc: '实线=required（理解 B 必须先读 A），虚线=recommended（读了更好），点线=related（有关联无依赖）。' },
    ],
  },
]

export default function HelpPanel({ onClose }: Props) {
  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(28,25,23,0.12)',
          zIndex: 29,
        }}
      />

      {/* Panel */}
      <div
        className="panel-slide-enter"
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: '42vw',
          minWidth: 460,
          maxWidth: 680,
          backgroundColor: 'var(--cm-bg-primary)',
          borderLeft: '1px solid var(--cm-border)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          zIndex: 30,
          boxShadow: '0 8px 32px rgba(28,25,23,0.12)',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '20px 24px',
            borderBottom: '1px solid var(--cm-border)',
            flexShrink: 0,
          }}
        >
          <h2
            style={{
              fontSize: 24,
              fontFamily: "'Cormorant Garamond', serif",
              fontWeight: 500,
              color: 'var(--cm-text-primary)',
              margin: 0,
            }}
          >
            Help
          </h2>
          <button
            onClick={onClose}
            style={{
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontSize: 20,
              color: 'var(--cm-text-secondary)',
              padding: '4px 8px',
              borderRadius: 2,
              lineHeight: 1,
              fontFamily: 'Raleway, sans-serif',
            }}
          >
            ✕
          </button>
        </div>

        {/* Scrollable content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
          {/* UI Guide */}
          <h3
            style={{
              fontSize: 16,
              fontFamily: "'Cormorant Garamond', serif",
              fontWeight: 600,
              color: 'var(--cm-accent)',
              marginBottom: 20,
              letterSpacing: '0.02em',
            }}
          >
            界面指南
          </h3>

          {UI_GUIDE.map((section) => (
            <div key={section.section} style={{ marginBottom: 24 }}>
              <h4
                style={{
                  fontSize: 13,
                  fontFamily: 'Raleway, sans-serif',
                  fontWeight: 600,
                  color: 'var(--cm-text-primary)',
                  margin: '0 0 8px 0',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  borderBottom: '1px solid var(--cm-border)',
                  paddingBottom: 6,
                }}
              >
                {section.section}
              </h4>
              {section.items.map((item) => (
                <div
                  key={item.name}
                  style={{
                    marginBottom: 6,
                    fontSize: 13,
                    lineHeight: 1.55,
                  }}
                >
                  <span
                    style={{
                      fontFamily: 'JetBrains Mono, monospace',
                      fontSize: 12,
                      color: 'var(--cm-text-primary)',
                      backgroundColor: 'var(--cm-bg-subtle)',
                      padding: '1px 6px',
                      borderRadius: 2,
                      marginRight: 8,
                    }}
                  >
                    {item.name}
                  </span>
                  <span style={{ color: 'var(--cm-text-secondary)', fontFamily: 'Raleway, sans-serif' }}>
                    {item.desc}
                  </span>
                </div>
              ))}
            </div>
          ))}

          {/* CLI Reference */}
          <h3
            style={{
              fontSize: 16,
              fontFamily: "'Cormorant Garamond', serif",
              fontWeight: 600,
              color: 'var(--cm-accent)',
              marginBottom: 20,
              marginTop: 32,
              letterSpacing: '0.02em',
            }}
          >
            CLI 命令参考
          </h3>

          <div style={{ fontSize: 13, fontFamily: 'Raleway, sans-serif', color: 'var(--cm-text-secondary)', marginBottom: 16 }}>
            以下 15 个命令通过 <code style={{ backgroundColor: 'var(--cm-bg-subtle)', padding: '1px 4px', borderRadius: 2, fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>codememory &lt;command&gt;</code> 在终端中使用。
            其中的 10 个已封装为 REST API 供前端调用——见下方 API 参考。
          </div>

          {CLI_COMMANDS.map(({ cmd, args, desc, layer }) => (
            <div
              key={cmd}
              style={{
                marginBottom: 10,
                paddingBottom: 10,
                borderBottom: '1px solid var(--cm-bg-subtle)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
                <code
                  style={{
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: 12,
                    color: 'var(--cm-text-primary)',
                    fontWeight: 500,
                  }}
                >
                  {cmd}
                </code>
                {args && (
                  <code
                    style={{
                      fontFamily: 'JetBrains Mono, monospace',
                      fontSize: 12,
                      color: 'var(--cm-text-tertiary)',
                    }}
                  >
                    {args}
                  </code>
                )}
                <span
                  style={{
                    fontSize: 9,
                    fontFamily: 'Raleway, sans-serif',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.06em',
                    color: 'var(--cm-accent)',
                    backgroundColor: 'var(--cm-bg-hover)',
                    padding: '1px 6px',
                    borderRadius: 2,
                    marginLeft: 'auto',
                    flexShrink: 0,
                  }}
                >
                  {layer}
                </span>
              </div>
              <div style={{ fontSize: 12, fontFamily: 'Raleway, sans-serif', color: 'var(--cm-text-secondary)', lineHeight: 1.5 }}>
                {desc}
              </div>
            </div>
          ))}

          {/* REST API Reference */}
          <h3
            style={{
              fontSize: 16,
              fontFamily: "'Cormorant Garamond', serif",
              fontWeight: 600,
              color: 'var(--cm-accent)',
              marginBottom: 20,
              marginTop: 32,
              letterSpacing: '0.02em',
            }}
          >
            REST API 端点
          </h3>

          <div style={{ fontSize: 13, fontFamily: 'Raleway, sans-serif', color: 'var(--cm-text-secondary)', marginBottom: 16 }}>
            前端通过以下端点与后端通信。所有端点委托 <code style={{ backgroundColor: 'var(--cm-bg-subtle)', padding: '1px 4px', borderRadius: 2, fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>src/codememory/handlers.py</code>，不重复实现业务逻辑。
          </div>

          {[
            { method: 'GET', path: '/api/memories', desc: '所有记忆摘要列表（id, type, summary, tags, intensity, maturity, directory）' },
            { method: 'GET', path: '/api/memories/{id}', desc: '单条记忆完整内容（frontmatter 所有字段 + body markdown）' },
            { method: 'GET', path: '/api/graph', desc: 'cytoscape 格式的节点 + 边数据，节点颜色/大小/边样式由此驱动' },
            { method: 'POST', path: '/api/resolve', desc: 'DAG 拓扑解析：body 传 {id, depth, budget}，返回排序节点列表 + 裁剪级别' },
            { method: 'POST', path: '/api/memories', desc: '创建新记忆，body 传 {id, summary, tags, intensity, body}，委托 handle_create()' },
            { method: 'PUT', path: '/api/memories/{id}', desc: '更新记忆，body 传 {change_note, body?, summary?, tags?, intensity?, status?}，委托 handle_update()' },
            { method: 'GET', path: '/api/stats', desc: '统计：总数、maturity 分布（draft/verified/proven）、stale 数量、tag 频次' },
            { method: 'POST', path: '/api/wander', desc: '加权随机召回一条冷记忆（低 access_count + 高 intensity），返回 summary + id' },
            { method: 'POST', path: '/api/validate', desc: '运行 validate()，返回诊断结果（循环/断链/schema/maturity 错误和警告）' },
          ].map((ep) => (
            <div
              key={ep.path + ep.method}
              style={{
                marginBottom: 8,
                paddingBottom: 8,
                borderBottom: '1px solid var(--cm-bg-subtle)',
                display: 'flex',
                alignItems: 'flex-start',
                gap: 10,
              }}
            >
              <span
                style={{
                  display: 'inline-block',
                  padding: '1px 6px',
                  borderRadius: 2,
                  fontSize: 9,
                  fontWeight: 600,
                  fontFamily: 'JetBrains Mono, monospace',
                  textTransform: 'uppercase',
                  color: ep.method === 'GET' ? 'var(--cm-success)' : ep.method === 'POST' ? 'var(--cm-info)' : 'var(--cm-warning)',
                  backgroundColor: ep.method === 'GET' ? 'var(--cm-bg-success-subtle)' : ep.method === 'POST' ? 'var(--cm-bg-info-subtle)' : 'var(--cm-bg-warning-subtle)',
                  minWidth: 36,
                  textAlign: 'center',
                  flexShrink: 0,
                  marginTop: 1,
                }}
              >
                {ep.method}
              </span>
              <div>
                <code style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: 'var(--cm-text-primary)' }}>
                  {ep.path}
                </code>
                <div style={{ fontSize: 12, fontFamily: 'Raleway, sans-serif', color: 'var(--cm-text-secondary)', lineHeight: 1.5, marginTop: 1 }}>
                  {ep.desc}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
