---
active: true
iteration: 1
session_id: 
max_iterations: 30
completion_promise: "LOOP_DONE"
started_at: "2026-03-23T15:08:57Z"
---

排查文字气泡位置不对或DPI缩放失效的问题，确保在多分辨率和高DPI下在鼠标附近正常展示

== PUA 行为协议（每次迭代必须遵守）==
1. 读取项目文件和 git log，了解上次做了什么
2. 按三条红线执行：闭环验证、事实驱动、穷尽一切方案
3. 跑 build/test 验证改动，不要跳过
4. 发现问题就修，修完再验证（不声称完成，先验证）
5. 扫描同类问题（冰山法则）
6. 只有当任务完全完成且验证通过时，输出 <promise>LOOP_DONE</promise>
禁止：
- 不要调用 AskUserQuestion
- 不要说"建议用户手动处理"
- 不要在未验证的情况下声称完成
- 遇到困难先穷尽所有自动化手段，不要用 <loop-abort> 逃避
