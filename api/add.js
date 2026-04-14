export default function handler(req, res) {
  const { a, b } = req.query;

  const numA = Number(a);
  const numB = Number(b);

  if (isNaN(numA) || isNaN(numB)) {
    return res.status(400).json({ error: "숫자를 입력하세요" });
  }

  res.status(200).json({ result: numA + numB });
}
