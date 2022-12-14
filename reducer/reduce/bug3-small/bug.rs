fn main() {
    let mut var1: (bool, f64, i32) = (false, 0.5f64, 100i32);
    let var2: &mut bool = &mut var1.0;
    *var2 = true;
    let var3: (bool, f64, i32) = var1;
    if (var3.0) {
        let var4 = 10i32;
        println!("{:?}", ("var4", var4));
    } else {
        let var5 = 1i32;
        println!("{:?}", ("var5", var5));
    }
}
