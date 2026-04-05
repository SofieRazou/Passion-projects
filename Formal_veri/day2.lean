-------Structurally inductive proof by pattern checking-------
theorem neq_nat_Self(n:Nat) :
  Nat.succ n ≠ n :=
  by
    induction n with
    |zero => simp
    | succ n' ih => simp

-----Binary trees-------
inductive BTree (α : Type) : Type where
  |empty : BTree α
  | node : α → BTree α → BTree α → BTree α

theorem ex1 (P Q: Prop) :
  P ∧ Q → P :=
  by
    intro hpq
    exact hpq.left

theorem ex2 (p q: Prop) :
  p → p ∨ q :=
  by
    intro hp
    apply Or.inl
    exact hp

theorem ex3 (p q r : Prop) :
  (p → q) → (q → r) → p → r :=
  by
    intro hpq hqr hp
    apply hqr
    apply hpq
    apply hp

theorem ex4 (p q: Prop) :
  p ∧ q → q ∧ p :=
  by
    intro h
    cases h with
    | intro hp hq => exact And.intro hq hp

theorem ex5 (p q : Prop) :
  (p → q) → (¬ q  → ¬ p) :=
  by
    intro hpq hnq hp
    apply hnq
    exact hpq hp

theorem ex6 {α : Type} [Nonempty α] (P Q : α → Prop) :
  (∀ x, P x → Q x) → (∀ x, P x) → (∀ x, Q x) :=
  by
    intro hpq hp x
    exact hpq x (hp x)

theorem ex7 (P Q R : Prop) :
  (P → R) → (Q → R) → (P ∨ Q) → R :=
by
  intro hPR hQR hPQ
  cases hPQ with
  | inl hP =>
      exact hPR hP
  | inr hQ =>
      exact hQR hQ

theorem ex8 (p q r : Prop) :
  (p → r) → (q → r) → (p ∧ q → r) :=
  by
    intro hpr hqr hpq
    cases hpq with
    |intro hp hq =>
      exact hpr hp

-----more Discrete math inspired--------
theorem dm1 (p q r: Prop) :
  (p → q) → (p → r) → p → q ∧ r :=
  by
    intro hpq hpr hp
    exact ⟨(hpq hp), (hpr hp)⟩

theorem dm2 (p q r: Prop) :
  (p ∧ q → r) → p → q → r :=
  by
    intro h hp hq
    exact h ⟨hp, hq⟩

theorem dm3 (p q r: Prop) :
  (p → r) → (q → r) → p ∨ q → r :=
by
  intro hpr hqr hpq
  cases hpq with
  | inl hp =>
      exact hpr hp
  | inr hq =>
      exact hqr hq

theorem dm4 (p q r : Prop) :
  (p → q ∧ r) → (p → q) ∧ (p → r) := by
  intro h
  exact ⟨
    (fun hp => (h hp).left),
    (fun hp => (h hp).right)
  ⟩
