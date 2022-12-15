#[inline(never)]
fn fun25(var574: Box<i32>) -> ! {
    fun25(var574)
}
fn main() {
    let var574 = Box::from(1745183449i32);
    fun25(var574);
}
