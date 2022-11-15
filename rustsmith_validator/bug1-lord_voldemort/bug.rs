macro_rules! reconditioned_div {
    ($a:expr,$b:expr, $zero: expr) => {{
        let denominator = $b;
        if (denominator != $zero) {
            ($a)
        } else {
            $zero
        }
    }};
}
struct Struct2 {
    var39: f32,
    var40: i16,
    var41: i16,
    var42: i128,
}
struct Struct5 {
    var197: i64,
    var198: i8,
}
struct Struct6 {
    var347: f32,
    var348: f32,
}
struct Struct7 {
    var395: bool,
    var396: i64,
}
struct Struct10 {
    var1126: f32,
    var1127: (f32, bool, i16),
    var1128: bool,
    var1129: i8,
    var1130: (Struct5, f32, Struct6, i32),
}
fn fun14(var453: (i8, i8, i128), var454: i16, var455: i64) {
    loop {}
}
fn fun19(var722: Struct7, var723: i8) -> i8 {
    27
}
fn main() {
    let var1115 = 48;
    let var1117 = 9147;
    let var1116 = Struct2 {
        var39: 0.62885755f32,
        var40: var1117,
        var41: 221,
        var42: 166824599952835012764483753652938212823,
    }
    .var42;
    let var1119 = 9153145817148623514;
    let var1118 = var1119;
    fun14((69, var1115, var1116), var1117, var1118);
    let var1131 = 0.24094963f32;
    let var1140: (bool, (f32, bool, i16), f64) = {
        let var1199 = true;
        (false, (0.7927916f32, var1199, 8656), 0.01559819904673998f64)
    };
    let var1139: (bool, (f32, bool, i16), f64) = var1140;
    let var1138: (f32, bool, i16) = var1139.1;
    let var1137: (f32, bool, i16) = var1138;
    let var1136: (f32, bool, i16) = var1137;
    let var1135: (f32, bool, i16) = var1136;
    let var1134: (f32, bool, i16) = var1135;
    let var1133: (f32, bool, i16) = var1134;
    let var1132: (f32, bool, i16) = var1133;
    let var1201 = false;
    let var1200 = var1201;
    let var1203 = Struct7 {
        var395: true,
        var396: var1118,
    };
    let var1202 = var1203;
    let var1210: (Struct6, f32, f32) = (
        Struct6 {
            var347: 0.46295255f32,
            var348: 0.3783806f32,
        },
        0.5751406f32,
        0.9929493f32,
    );
    let var1209: (Struct6, f32, f32) = var1210;
    let var1208: (Struct6, f32, f32) = var1209;
    let var1204: (Struct5, f32, Struct6, i32) = (
        Struct5 {
            var197: 1752997539984291370,
            var198: var1115,
        },
        reconditioned_div!(0.028511405f32, var1208.2, 0.0f32),
        Struct6 {
            var347: var1131,
            var348: 0.83879215f32,
        },
        1156417715,
    );
    Struct10 {
        var1126: var1131,
        var1127: var1132,
        var1128: var1200,
        var1129: fun19(var1202, var1115),
        var1130: var1204,
    };
}
