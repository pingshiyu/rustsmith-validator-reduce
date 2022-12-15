struct a ;
impl a {
  fn b() -> Option<u16> {
    let c= (5,);
    let d: Option<Option<i8>> = None;
    Some(match d {e =>c.0})
  }
}
fn main() { }
