const fs = require("fs");
const files = [
  "c:/Users/stuti/OneDrive/Desktop/FunWithArts/funwithart-main/studio.html",
  "c:/Users/stuti/OneDrive/Desktop/FunWithArts/funwithart-main/wishlist.html",
];
const close = "</" + String.fromCharCode(100, 105, 118) + ">";
const open = "<" + String.fromCharCode(100, 105, 118);
for (const p of files) {
  let t = fs.readFileSync(p, "utf8");
  t = t.replace(/<\/motion>/g, close);
  t = t.replace(/<motion /g, open + " ");
  t = t.replace(/<motion>/g, open + ">");
  fs.writeFileSync(p, t);
}
