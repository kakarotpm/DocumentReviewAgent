// Half-circle gauge showing the score out of 100, with a marker at the pass threshold.

const RADIUS = 80;
const CENTER = { x: 100, y: 100 };

// Point on the arc for a value 0–100 (0 = left end, 100 = right end).
function point(value, radius = RADIUS) {
  const angle = Math.PI * (1 - value / 100);
  return { x: CENTER.x + radius * Math.cos(angle), y: CENTER.y - radius * Math.sin(angle) };
}

function arc(from, to) {
  const start = point(from);
  const end = point(to);
  return `M ${start.x} ${start.y} A ${RADIUS} ${RADIUS} 0 0 1 ${end.x} ${end.y}`;
}

export default function ScoreGauge({ score, threshold, passed }) {
  const color = passed ? "stroke-emerald-500" : "stroke-red-500";
  const inner = point(threshold, RADIUS - 14);
  const outer = point(threshold, RADIUS + 14);
  const label = point(threshold, RADIUS + 26);
  return (
    <svg viewBox="0 0 200 120" className="w-full max-w-64" role="img" aria-label={`Score ${score} out of 100; pass mark ${threshold}`}>
      <path d={arc(0, 100)} className="stroke-slate-200 dark:stroke-slate-700" strokeWidth="16" fill="none" strokeLinecap="round" />
      {score > 0 && <path d={arc(0, Math.min(score, 100))} className={color} strokeWidth="16" fill="none" strokeLinecap="round" />}
      <line x1={inner.x} y1={inner.y} x2={outer.x} y2={outer.y} className="stroke-slate-700 dark:stroke-slate-300" strokeWidth="2" />
      <text x={label.x} y={label.y} textAnchor="middle" className="fill-slate-500 text-[9px]">{threshold}</text>
      <text x="100" y="92" textAnchor="middle" className="fill-slate-900 text-[40px] font-semibold dark:fill-slate-50">{score}</text>
      <text x="100" y="112" textAnchor="middle" className="fill-slate-500 text-[11px]">out of 100</text>
    </svg>
  );
}
