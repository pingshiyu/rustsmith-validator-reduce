use std::env;
struct a {
    b: String,
}
struct c {
    d: Option<Option<u32>>,
    e: ((f64, Vec<i64>, Option<f32>, Box<a>), Box<a>, u8),
    f: i32,
}
fn main() {
    let aa: Vec<String> = env::args().collect();
    let af = aa[7].parse().unwrap();
    match None::<Vec<i32>> {
        g => {
            {
                let h = None;
                let i: ((f64, Vec<i64>, Option<f32>, Box<a>), Box<a>, u8) = (
                    (
                        aa[4].parse().unwrap(),
                        vec![],
                        None,
                        Box::new(a {
                            b: aa[2].parse().unwrap(),
                        }),
                    ),
                    Box::new(a {
                        b: aa[2].parse().unwrap(),
                    }),
                    8,
                );
                let mut j = c { d: h, e: i, f: 7 };
                let k = &mut j;
                let l = aa[9].parse().unwrap();
                let ah = vec![];
                let ai = ah;
                let aj = ai;
                let ak = aj;
                let al = ak;
                let am = al;
                let an = am;
                let ao = an;
                let ap = ao;
                let aq = ap;
                let ar = aq;
                let v = ar;
                let m = v;
                let var823 = aa[2].parse().unwrap();
                let o = a { b: var823 };
                let p = o;
                let n = Box::new(p);
                let q: (f64, Vec<i64>, Option<f32>, Box<a>) =
                    (aa[4].parse().unwrap(), m, Some(aa[5].parse().unwrap()), n);
                let r = String::from("");
                let s = a { b: r };
                let w = s;
                let t = c {
                    d: h,
                    e: (q, Box::new(w), 8),
                    f: l,
                };
                *k = t
            }
            let u: (i16, usize) = (
                match 0 {
                    g => 4,
                },
                af,
            );
        }
    }
}
