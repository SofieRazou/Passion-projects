import Mathlib.Data.List.Basic
import Mathlib.Data.List.Perm
import Mathlib.Tactic

open List

/-
Base: + 1 edge has degrees [1,1]
Step: adding a new leaf increases one existing degree by 1
and adds a new degree 1
-/

inductive TreeDegSeq : List Nat → Prop where
| base :
    TreeDegSeq [1, 1]

| addLeaf :
    TreeDegSeq ds →
    j < ds.length →
    TreeDegSeq ((ds.modifyNth j (fun d => d + 1)) ++ [1])

| perm :
    ds.Perm ds' →
    TreeDegSeq ds →
    TreeDegSeq ds'

namespace TreeDegSeq

/-
Auxiliary  lemmas
-/

axiom sum_modifyNth_add_one
    (ds : List Nat) (j : Nat) (hj : j < ds.length) :
    (ds.modifyNth j (fun d => d + 1)).sum = ds.sum + 1

axiom length_modifyNth
    (ds : List Nat) (j : Nat) :
    (ds.modifyNth j (fun d => d + 1)).length = ds.length

axiom pos_modifyNth_add_one
    {ds : List Nat} {j : Nat}
    (hpos : ∀ d ∈ ds, d ≥ 1) :
    ∀ d ∈ ds.modifyNth j (fun d => d + 1), d ≥ 1

axiom perm_sum
    {ds ds' : List Nat}
    (h : ds.Perm ds') :
    ds.sum = ds'.sum

axiom perm_length
    {ds ds' : List Nat}
    (h : ds.Perm ds') :
    ds.length = ds'.length

axiom perm_pos
    {ds ds' : List Nat}
    (h : ds.Perm ds')
    (hpos : ∀ d ∈ ds, d ≥ 1) :
    ∀ d ∈ ds', d ≥ 1

/-
Forward direction:
-/

theorem pos :
    ∀ {ds : List Nat},
      TreeDegSeq ds →
      ∀ d ∈ ds, d ≥ 1
| _, base => by
    intro d hd
    simp at hd
    omega

| _, addLeaf h hj => by
    intro d hd
    simp at hd

    cases hd with
    | inl hOld =>
        exact pos_modifyNth_add_one (pos h) d hOld
    | inr hNew =>
        omega

| _, perm hp h => by
    exact perm_pos hp (pos h)


theorem sum_eq :
    ∀ {ds : List Nat},
      TreeDegSeq ds →
      ds.sum = 2 * (ds.length - 1)
| _, base => by
    simp

| _, addLeaf h hj => by
    have ih := sum_eq h

    have hsum1 :
        (ds.modifyNth j (fun d => d + 1)).sum = ds.sum + 1 :=
      sum_modifyNth_add_one ds j hj

    have hsum2 :
        ((ds.modifyNth j (fun d => d + 1)) ++ [1]).sum = ds.sum + 2 := by
      simp [hsum1]

    have hlen :
        ((ds.modifyNth j (fun d => d + 1)) ++ [1]).length = ds.length + 1 := by
      simp [length_modifyNth]

    rw [hsum2, hlen, ih]
    omega

| _, perm hp h => by
    have ih := sum_eq h
    have hs := perm_sum hp
    have hl := perm_length hp

    rw [← hs, ← hl]
    exact ih


theorem forward
    {ds : List Nat}
    (h : TreeDegSeq ds) :
    (∀ d ∈ ds, d ≥ 1) ∧
    ds.sum = 2 * (ds.length - 1) := by
  constructor
  · exact pos h
  · exact sum_eq h


/-
Backward direction
-/

axiom backward
    (ds : List Nat)
    (hlen : ds.length ≥ 2)
    (hpos : ∀ d ∈ ds, d ≥ 1)
    (hsum : ds.sum = 2 * (ds.length - 1)) :
    TreeDegSeq ds


/-
Final theorem:
A list is a tree degree sequence iff all entries are positive
and the sum is 2(n-1)
-/

theorem tree_degree_sequence_iff
    (ds : List Nat)
    (hlen : ds.length ≥ 2) :
    TreeDegSeq ds ↔
      (∀ d ∈ ds, d ≥ 1) ∧
      ds.sum = 2 * (ds.length - 1) := by
  constructor

  · intro h
    exact forward h

  · intro h
    exact backward ds hlen h.left h.right

end TreeDegSeq
