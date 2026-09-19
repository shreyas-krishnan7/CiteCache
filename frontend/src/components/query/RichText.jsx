// Renders the model's answer: paragraphs, "* " / "- " bullet lists, **bold**,
// and section references ("section 22(2)") highlighted like citations.
const INLINE = /(\*\*[^*]+\*\*|\b[Ss]ections? \d+[A-Za-z]?(?:\([0-9a-z]+\))*)/g;

function Inline({ text }) {
  return text.split(INLINE).map((part, i) => {
    if (!part) return null;
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>;
    if (/^[Ss]ections? \d/.test(part)) {
      return <span key={i} className="rounded bg-blue-50 px-1 text-blue-700">{part}</span>;
    }
    return part;
  });
}

export default function RichText({ text }) {
  const blocks = [];
  let list = null;
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    const bullet = line.match(/^[*-]\s+(.*)/);
    if (bullet) {
      if (!list) blocks.push((list = { type: "ul", items: [] }));
      list.items.push(bullet[1]);
    } else if (line) {
      list = null;
      blocks.push({ type: "p", text: line });
    } else {
      list = null;
    }
  }
  return (
    <div className="space-y-5 text-[17px] leading-[1.8] text-slate-800">
      {blocks.map((b, i) =>
        b.type === "ul" ? (
          <ul key={i} className="list-disc space-y-2 pl-6 marker:text-slate-400">
            {b.items.map((it, j) => <li key={j}><Inline text={it} /></li>)}
          </ul>
        ) : (
          <p key={i}><Inline text={b.text} /></p>
        ),
      )}
    </div>
  );
}
