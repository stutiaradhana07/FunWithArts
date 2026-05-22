import pathlib
p = pathlib.Path(r"c:\Users\stuti\OneDrive\Desktop\FunWithArts\funwithart-main\login.html")
t = p.read_text(encoding="utf-8")
bad_o = "<" + "motion" + ">"
bad_c = "</" + "motion" + ">"
good_o = "<" + "div" + ">"
good_c = "</" + "motion" + ">"
good_c = "</" + "motion" + ">"
