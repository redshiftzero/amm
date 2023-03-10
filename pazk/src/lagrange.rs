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

/// Represents a Lagrange Basis Polynomial
pub struct LagrangeBasisPolynomial {
    /// The ith Lagrange Basis Polynomial
    pub i: usize,
    /// Max degree of the polynomial is n - 1
    pub n: usize,
}

impl LagrangeBasisPolynomial {
    /// Evaluate this polynomial at a given field element.
    pub fn evaluate(&self, X: Fq) -> Fq {
        let mut res = Fq::one();
        for j in 0..self.i {
            res *= (X - Fq::from(j as i128)) / (Fq::from(self.i as i128) - Fq::from(j as i128));
        }
        for j in self.i + 1..(self.n) {
            res *= (X - Fq::from(j as i128)) / (Fq::from(self.i as i128) - Fq::from(j as i128));
        }
        res
    }
}

/// Represents a polynomial in monomial basis, i.e. $a_0 + a_1x + a_2x^2 ...$
pub struct MonomialBasisPolynomial {
    /// Vector of coefficients
    pub a: Vec<Fq>,
}

impl MonomialBasisPolynomial {
    /// Evaluate this polynomial using monomial basis at a given field element.
    pub fn evaluate(&self, X: Fq) -> Fq {
        let mut res = Fq::zero();
        let mut X_pow = Fq::one();
        for a in self.a.iter() {
            res += *a * X_pow;
            X_pow *= X;
        }
        res
    }

    /// Use Lagrange basis polynomials to get the Xth coefficient.
    fn lagrange_coeff(&self, X: Fq) -> Fq {
        let mut res = Fq::zero();
        let n = self.a.len();
        for j in 0..n - 1 {
            let l = LagrangeBasisPolynomial { i: j, n };
            res += self.a[j + 1] * l.evaluate(X);
        }
        res
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lagrange_basis_polynomial() {
        let l0 = LagrangeBasisPolynomial { i: 0, n: 4 };
        assert_eq!(l0.evaluate(Fq::from(0)), Fq::one());
        assert_eq!(l0.evaluate(Fq::from(1)), Fq::zero());
        assert_eq!(l0.evaluate(Fq::from(2)), Fq::zero());

        let l1 = LagrangeBasisPolynomial { i: 1, n: 4 };
        assert_eq!(l1.evaluate(Fq::from(0)), Fq::zero());
        assert_eq!(l1.evaluate(Fq::from(1)), Fq::one());
        assert_eq!(l1.evaluate(Fq::from(2)), Fq::zero());
    }

    #[test]
    fn polynomial_representation() {
        let p = MonomialBasisPolynomial {
            a: vec![Fq::one(), Fq::one(), Fq::one(), Fq::one()],
        };
        assert_eq!(p.evaluate(Fq::from(0)), Fq::from(1));
        assert_eq!(p.evaluate(Fq::from(1)), Fq::from(4));
        assert_eq!(p.evaluate(Fq::from(2)), Fq::from(15));

        assert_eq!(Fq::from(1), p.lagrange_coeff(Fq::from(0)));
        assert_eq!(Fq::from(1), p.lagrange_coeff(Fq::from(1)));
        assert_eq!(Fq::from(1), p.lagrange_coeff(Fq::from(2)));
    }

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
