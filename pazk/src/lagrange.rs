use ark_bls12_377::Fq;
use ark_ff::{One, Zero};

// Lemma 3.6: Lagrange interpolation of multilinear polynomials
// The multilinear polynomial f~ extends f

pub fn number_to_bitvec(i: usize, n: usize) -> Vec<bool> {
    format!("{:0>width$}", format!("{:b}", i), width = n)
        .chars()
        .map(|x| x == '1')
        .collect()
}

/// Eqn 3.1
pub fn multilinear_f(x: &Vec<i128>, fws: &Vec<i128>) -> Fq {
    // fws are the v evaluations of f, i.e. f(w)
    // There are also v elements in w and v elements in x
    let v = x.len();
    assert_eq!(fws.len(), v);

    let res: i128 = fws
        .iter()
        .enumerate()
        .map(|(i, fw)| fw * chi_w(&number_to_bitvec(i, v), x))
        .sum();

    Fq::from(res)
}

/// Eqn 3.2
fn chi_w(w: &Vec<bool>, x: &Vec<i128>) -> i128 {
    assert_eq!(w.len(), x.len());

    let res: i128 = w
        .iter()
        .zip(x.iter())
        .map(|(&w, &x)| (x * i128::from(w) + (1 - x) * (1 - i128::from(w))))
        .product();

    res
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn simple_lemma37() {
        assert_eq!(number_to_bitvec(4, 3), vec![true, false, false]);
        assert_eq!(number_to_bitvec(4, 4), vec![false, true, false, false]);

        // f(0) = 0, f(1) = 0
        let f_tilde = multilinear_f(&vec![0, 1], &vec![0, 0]);
        assert_eq!(f_tilde, Fq::zero());

        // f(0) = 1, f(1) = 1
        let f_tilde = multilinear_f(&vec![0, 1], &vec![1, 1]);
        assert_eq!(f_tilde, Fq::one());
    }
}
