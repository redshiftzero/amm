//! bits of plonk

use ark_bls12_377::Fq;
use ark_ff::{One, Zero};

struct CommonPreprocessedInput {
    /// Number of gates in the circuit.
    pub(crate) n: usize,
}

struct PublicInput {
    /// Number of public inputs.
    pub(crate) l: u64,

    /// Wire values for public inputs. Length l.
    pub(crate) pi: Vec<Fq>,
}

struct Prover {
    pub(crate) pi: PublicInput,
    pub(crate) common: CommonPreprocessedInput,
}

struct Verifier {
    pub(crate) pi: PublicInput,
    pub(crate) common: CommonPreprocessedInput,
}

/// Helper to build a PLONK circuit.
struct CircuitBuilder {
    // Wire values
    a: Vec<Fq>,
    b: Vec<Fq>,
    c: Vec<Fq>,

    // Selectors
    pub q_l: Vec<Fq>,
    pub q_r: Vec<Fq>,
    pub q_o: Vec<Fq>,
    pub q_m: Vec<Fq>,
    pub q_c: Vec<Fq>,
}

impl CircuitBuilder {
    pub fn add_gate(&mut self, gate: Gate) {
        // Check if valid. only add if it is valid
        todo!()
    }

    pub fn public_inputs(&self) -> PublicInput {
        todo!()
    }

    pub fn common_preprocessed_input(&self) -> CommonPreprocessedInput {
        todo!()
    }
}

/// Represents an individual gate in a PLONK circuit.
struct Gate {
    /// Left wire selector.
    pub(crate) q_l: Fq,
    /// Right wire selector.
    pub(crate) q_r: Fq,
    /// Output wire selector.
    pub(crate) q_o: Fq,
    /// Multiplication selector.
    pub(crate) q_m: Fq,
    /// Constant selector.
    pub(crate) q_c: Fq,
}

impl Gate {
    /// Create an addition gate.
    pub fn addition_gate() -> Gate {
        Gate {
            q_l: Fq::one(),
            q_r: Fq::one(),
            q_o: -Fq::one(),
            q_m: Fq::zero(),
            q_c: Fq::zero(),
        }
    }

    /// Create a multiplication gate.
    pub fn multiplication_gate() -> Gate {
        Gate {
            q_l: Fq::zero(),
            q_r: Fq::zero(),
            q_o: -Fq::one(),
            q_m: Fq::one(),
            q_c: Fq::zero(),
        }
    }

    /// Create a constant gate.
    pub fn constant_gate(value: Fq) -> Gate {
        Gate {
            q_l: Fq::one(),
            q_r: Fq::zero(),
            q_o: Fq::zero(),
            q_m: Fq::zero(),
            q_c: value,
        }
    }

    /// Check the basic PLONK constraint equation holds for this gate and wire values.
    pub fn check_constraint_eqn(&self, a: Fq, b: Fq, c: Fq) -> bool {
        self.q_l * a + self.q_r * b + self.q_o * c + self.q_m * a * b + self.q_c == Fq::zero()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn define_addition_gate() {
        // Check 1 + 1 = 2 AKA 1 + 1 - 2 = 0
        let expected_output = Fq::one() + Fq::one();
        let gate = Gate::addition_gate();
        assert!(gate.check_constraint_eqn(Fq::one(), Fq::one(), expected_output),);
    }
}
