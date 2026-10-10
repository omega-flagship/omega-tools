;; ============================================================================
;; lib_omegaclaw_goal_composition.metta — bounded target-outcome composition
;;
;; Pure MeTTa / PeTTa-compatible Loop-3 research kernel. A supplied target is
;; expanded backwards by forward execution over explicit hypothetical nodes.
;; Inputs and state are immutable terms; no space, capability, or channel is
;; mutated. The result is an advisory proof episode, never effect authority.
;; ============================================================================

;; This module is the Goal Weaver.  In addition to bounded proof search it
;; owns the executable, authority-inert goal-lifecycle transition contract.
;; ECAN/TECAN, MetaMo/OpenPsi and PVF may contribute admitted evidence to this
;; boundary; none of them may write a transition or successor intent directly.

;; Card shape:
;;   (readiness-card ID OUTPUT (PREREQUISITE ...) AUTHORITY)
;; Admission is a separate list of card IDs supplied by AttentionBank/ECAN.
;; This kernel cannot admit a card or upgrade its authority.

;; Budgets:
;;   proof-size — maximum cards in one proof (primary search fuel)
;;   node-steps — maximum explicit frontier transitions
;;   candidates — maximum card records inspected across the episode
;;   frontier — maximum pending hypothetical nodes
;;   answers — maximum completed proof answers
;; Elapsed time, RSS, and output bytes are enforced by the process wrapper;
;; pure MeTTa has no trusted elapsed-time or process-memory primitive.

;; ----------------------------------------------------------------------------
;; 1. Closed list and card helpers
;; ----------------------------------------------------------------------------

(= (loop3-member? $item $items)
   (if (== $items ())
       False
       (if (== $item (car-atom $items))
           True
           (loop3-member? $item (cdr-atom $items)))))

(= (loop3-append $left $right)
   (if (== $left ())
       $right
       (cons-atom (car-atom $left)
                  (loop3-append (cdr-atom $left) $right))))

(= (loop3-reverse-onto $items $out)
   (if (== $items ())
       $out
       (loop3-reverse-onto
         (cdr-atom $items) (cons-atom (car-atom $items) $out))))

(= (loop3-reverse $items) (loop3-reverse-onto $items ()))

;; ----------------------------------------------------------------------------
;; 1a. Executable goal lifecycle (the adopted ten-state FSM)
;; ----------------------------------------------------------------------------

;; (GoalLifecycleStateV1
;;   EPISODE VERSION STATE GOAL NEXT-DIRECTION BLOCKERS LAST-VERIFIED
;;   PROGRESS-COUNT ATTEMPTS STALE-CYCLES STOP-RULE PROVENANCE)
;;
;; (GoalProgressEvidenceV1
;;   EPISODE VERSION EVIDENCE-ID RESULT-REF SIGNAL VERIFICATION)
;;
;; SIGNAL is a typed admitted event, never free provider continuation prose.
;; The reducer deliberately carries the state's current next direction for
;; ordinary progress. Only native lifecycle outcomes replace it with one of
;; the closed directions below.

(= (goal-life-second $value) (car-atom (cdr-atom $value)))
(= (goal-life-third $value) (car-atom (cdr-atom (cdr-atom $value))))
(= (goal-life-fourth $value)
   (car-atom (cdr-atom (cdr-atom (cdr-atom $value)))))
(= (goal-life-fifth $value)
   (car-atom (cdr-atom (cdr-atom (cdr-atom (cdr-atom $value))))))
(= (goal-life-sixth $value)
   (car-atom
     (cdr-atom (cdr-atom (cdr-atom (cdr-atom (cdr-atom $value)))))))
(= (goal-life-seventh $value)
   (car-atom
     (cdr-atom
       (cdr-atom (cdr-atom (cdr-atom (cdr-atom (cdr-atom $value))))))))
(= (goal-life-eighth $value)
   (car-atom
     (cdr-atom
       (cdr-atom
         (cdr-atom
           (cdr-atom (cdr-atom (cdr-atom (cdr-atom $value)))))))))
(= (goal-life-ninth $value)
   (car-atom
     (cdr-atom
       (cdr-atom
         (cdr-atom
           (cdr-atom
             (cdr-atom (cdr-atom (cdr-atom (cdr-atom $value))))))))))
(= (goal-life-tenth $value)
   (car-atom
     (cdr-atom
       (cdr-atom
         (cdr-atom
           (cdr-atom
             (cdr-atom
               (cdr-atom (cdr-atom (cdr-atom (cdr-atom $value)))))))))))
(= (goal-life-eleventh $value)
   (car-atom
     (cdr-atom
       (cdr-atom
         (cdr-atom
           (cdr-atom
             (cdr-atom
               (cdr-atom
                 (cdr-atom (cdr-atom (cdr-atom (cdr-atom $value))))))))))))
(= (goal-life-twelfth $value)
   (car-atom
     (cdr-atom
       (cdr-atom
         (cdr-atom
           (cdr-atom
             (cdr-atom
               (cdr-atom
                 (cdr-atom
                   (cdr-atom (cdr-atom (cdr-atom (cdr-atom $value)))))))))))))
(= (goal-life-thirteenth $value)
   (car-atom
     (cdr-atom
       (cdr-atom
         (cdr-atom
           (cdr-atom
             (cdr-atom
               (cdr-atom
                 (cdr-atom
                   (cdr-atom
                     (cdr-atom (cdr-atom (cdr-atom (cdr-atom $value))))))))))))))

(= (goal-life-state-name? $state)
   (or (== $state dormant)
     (or (== $state candidate)
       (or (== $state accepted)
         (or (== $state active)
           (or (== $state executing)
             (or (== $state verifying)
               (or (== $state completed)
                 (or (== $state abandoned)
                   (or (== $state failed) (== $state paused)))))))))))

(= (goal-life-stop-rule-shape? $rule)
   (if (not (is-expr $rule))
       False
       (and (== (size-atom $rule) 3)
         (and (== (car-atom $rule) GoalStopRuleV1)
           (and (not (== (goal-life-third $rule) none))
             (and
               (if (== (goal-life-second $rule) cycle-count)
                   (and (== (get-type (goal-life-third $rule)) Number)
                        (> (goal-life-third $rule) 0))
                   True)
               (or (== (goal-life-second $rule) metric-threshold)
                 (or (== (goal-life-second $rule) artifact-complete)
                   (or (== (goal-life-second $rule) cycle-count)
                     (or (== (goal-life-second $rule) bout-fuse)
                         (== (goal-life-second $rule) falsification)))))))))))

(= (goal-life-state-shape? $state)
   (if (not (is-expr $state))
       False
       (and (== (size-atom $state) 13)
         (and (== (car-atom $state) GoalLifecycleStateV1)
           (and (not (== (goal-life-second $state) none))
             (and (not (== (goal-life-third $state) none))
               (and (goal-life-state-name? (goal-life-fourth $state))
                 (and (not (== (goal-life-fifth $state) none))
                   (and (not (== (goal-life-sixth $state) none))
             (and (is-expr (goal-life-seventh $state))
                       (and (== (get-type (goal-life-ninth $state)) Number)
                         (and (== (get-type (goal-life-tenth $state)) Number)
                           (and (== (get-type (goal-life-eleventh $state)) Number)
                             (and (>= (goal-life-ninth $state) 0)
                               (and (>= (goal-life-tenth $state) 0)
                                 (and (>= (goal-life-eleventh $state) 0)
                                   (and (goal-life-stop-rule-shape?
                                          (goal-life-twelfth $state))
                                        (not (== (goal-life-thirteenth $state)
                                                 none)))))))))))))))))))

(= (goal-life-evidence-shape? $evidence)
   (if (not (is-expr $evidence))
       False
       (and (== (size-atom $evidence) 7)
            (== (car-atom $evidence) GoalProgressEvidenceV1))))

(= (goal-life-refuse $episode $version $reason $evidence-id)
   (GoalTransitionRefusalV1
     $episode $version $reason $evidence-id inspect-simulate))

(= (goal-life-decision
      $state $successor-version $to-state $decision $evidence
      $next-direction $progress-count $attempts $stale-cycles)
   (GoalTransitionDecisionV1
     (goal-life-second $state)
     (goal-life-third $state)
     $successor-version
     (goal-life-fifth $state)
     (goal-life-fourth $state)
     $to-state
     $decision
     (goal-life-fourth $evidence)
     (goal-life-fifth $evidence)
     $next-direction
     $progress-count
     $attempts
     $stale-cycles
     (goal-life-twelfth $state)
     inspect-simulate))

(= (goal-life-final-step? $stop-rule $next-progress-count)
   (if (and (== (goal-life-second $stop-rule) cycle-count)
            (>= (+ $next-progress-count 1)
                (goal-life-third $stop-rule)))
       True
       False))

(= (goal-life-step-matched $state $evidence $successor-version)
   (let* (($from-state (goal-life-fourth $state))
          ($signal (goal-life-sixth $evidence))
          ($verification (goal-life-seventh $evidence))
          ($direction (goal-life-sixth $state))
          ($progress (goal-life-ninth $state))
          ($attempts (goal-life-tenth $state))
          ($stale (goal-life-eleventh $state))
          ($next-progress (+ $progress 1))
          ($next-attempt (+ $attempts 1))
          ($next-stale (+ $stale 1)))
     (if (== $signal conscious-abandon)
         (goal-life-decision
           $state $successor-version abandoned abandon $evidence
           archive-goal $progress $attempts $stale)
       (if (and (== $from-state dormant) (== $signal curiosity-trigger))
           (goal-life-decision
             $state $successor-version candidate propose-candidate $evidence
             $direction $progress $attempts 0)
       (if (and (== $from-state candidate) (== $signal candidate-qualified))
           (goal-life-decision
             $state $successor-version accepted accept-candidate $evidence
             $direction $progress $attempts 0)
       (if (and (== $from-state candidate) (== $signal candidate-rejected))
           (goal-life-decision
             $state $successor-version dormant reject-candidate $evidence
             park-goal $progress $attempts $stale)
       (if (and (== $from-state accepted) (== $signal priority-selected))
           (goal-life-decision
             $state $successor-version active foreground $evidence
             $direction $progress $attempts 0)
       (if (and (== $from-state active) (== $signal action-ready))
           (goal-life-decision
             $state $successor-version executing execute $evidence
             $direction $progress $attempts 0)
       (if (and (== $from-state executing) (== $signal output-produced))
           (goal-life-decision
             $state $successor-version verifying verify $evidence
             verify-latest-result $progress $attempts 0)
       (if (and (== $from-state verifying) (== $signal completion-met))
           (if (== $verification stranger-verifiable)
               (goal-life-decision
                 $state $successor-version completed complete $evidence
                 summarize-completed-goal $next-progress $attempts 0)
               (goal-life-refuse
                 (goal-life-second $state) (goal-life-third $state)
                 completion-not-stranger-verifiable
                 (goal-life-fourth $evidence)))
       (if (and (== $from-state verifying) (== $signal partial-progress))
           (goal-life-decision
             $state $successor-version active
             (if (goal-life-final-step?
                   (goal-life-twelfth $state) $next-progress)
                 continue-final-step continue)
             $evidence
             (if (goal-life-final-step?
                   (goal-life-twelfth $state) $next-progress)
                 summarize-accumulated-result $direction)
             $next-progress 0 0)
       (if (and (== $from-state verifying) (== $signal retry-needed))
           (if (>= $next-attempt 3)
               (goal-life-decision
                 $state $successor-version failed fail-bounded-retries
                 $evidence reframe-or-switch $progress $next-attempt 0)
               (goal-life-decision
                 $state $successor-version active retry $evidence
                 $direction $progress $next-attempt 0))
       ;; Foreground arrival is priority evidence, not failure evidence.  The
       ;; paused goal retains its exact direction, progress, attempt count and
       ;; staleness count so a conversation can interrupt a cognitive bout
       ;; without erasing it or charging a retry.  The physical carrier may
       ;; report arrival, but this native reducer alone owns the transition.
       (if (and (or (== $from-state active) (== $from-state executing))
                (and (== $signal foreground-preempted)
                     (== $verification primary-ingress-admission-bound)))
           (goal-life-decision
             $state $successor-version paused pause-foreground $evidence
             $direction $progress $attempts $stale)
       (if (and (== $from-state paused)
                (and (== $signal foreground-settled)
                     (== $verification foreground-preemption-bound)))
           (goal-life-decision
             $state $successor-version active resume-foreground $evidence
             $direction $progress $attempts $stale)
       (if (and (or (== $from-state active) (== $from-state executing))
                (or (== $signal dependency-blocked)
                    (== $signal resource-exhausted)))
           (goal-life-decision
             $state $successor-version paused pause-blocked $evidence
             wait-for-resolution $progress $attempts $stale)
       (if (and (== $from-state paused)
                (or (== $signal dependency-resolved)
                    (== $signal resource-restored)))
           (goal-life-decision
             $state $successor-version active resume $evidence
             $direction $progress $attempts 0)
       (if (and (== $from-state active) (== $signal no-progress))
           (if (>= $next-stale 10)
               (goal-life-decision
                 $state $successor-version paused pause-stale $evidence
                 reframe-or-switch $progress $attempts $next-stale)
               (goal-life-decision
                 $state $successor-version active wait-for-evidence $evidence
                 $direction $progress $attempts $next-stale))
       (if (and (or (== $from-state completed)
                    (or (== $from-state abandoned) (== $from-state failed)))
                (== $signal backlog-recompute))
           (goal-life-decision
             $state $successor-version dormant archive $evidence
             park-goal $progress $attempts $stale)
           (goal-life-refuse
             (goal-life-second $state) (goal-life-third $state)
             transition-not-admitted (goal-life-fourth $evidence))))))))))))))))))))

;; Exact current-version binding prevents a stale provider result from driving
;; a newer goal head. Successor versions are coordinator inputs but must be
;; present and distinct; the LivingIntent organ separately checks the complete
;; successor head against this decision.
(= (goal-life-step $state $evidence $successor-version)
   (if (not (goal-life-state-shape? $state))
       (goal-life-refuse none none invalid-state unknown-evidence)
       (if (not (goal-life-evidence-shape? $evidence))
           (goal-life-refuse
             (goal-life-second $state) (goal-life-third $state)
             invalid-evidence unknown-evidence)
           (if (not (== (goal-life-second $state)
                         (goal-life-second $evidence)))
               (goal-life-refuse
                 (goal-life-second $state) (goal-life-third $state)
                 wrong-episode (goal-life-fourth $evidence))
               (if (not (== (goal-life-third $state)
                             (goal-life-third $evidence)))
                   (goal-life-refuse
                     (goal-life-second $state) (goal-life-third $state)
                     stale-evidence (goal-life-fourth $evidence))
                   (if (or (== $successor-version none)
                           (== $successor-version (goal-life-third $state)))
                       (goal-life-refuse
                         (goal-life-second $state) (goal-life-third $state)
                         invalid-successor-version
                         (goal-life-fourth $evidence))
                       (goal-life-step-matched
                         $state $evidence $successor-version)))))))

(= (goal-life-output-authority $value) inspect-simulate)
(= (goal-life-can-grant-effect? $value) False)

(= (loop3-card-id
      (readiness-card $id $output $prerequisites $authority))
   $id)
(= (loop3-card-output
      (readiness-card $id $output $prerequisites $authority))
   $output)
(= (loop3-card-prerequisites
      (readiness-card $id $output $prerequisites $authority))
   $prerequisites)
(= (loop3-card-authority
      (readiness-card $id $output $prerequisites $authority))
   $authority)

(= (loop3-card-admitted? $card $admitted-card-ids)
   (and (== (loop3-card-authority $card) inspect-simulate)
        (loop3-member? (loop3-card-id $card) $admitted-card-ids)))

;; Card identity is part of the frozen input contract. Rejecting duplicate IDs
;; keeps exact-node dedup from silently collapsing two purportedly distinct
;; cards with indistinguishable plans.
(= (loop3-card-id-member? $id $cards)
   (if (== $cards ())
       False
       (if (== $id (loop3-card-id (car-atom $cards)))
           True
           (loop3-card-id-member? $id (cdr-atom $cards)))))

(= (loop3-card-ids-unique? $cards)
   (if (== $cards ())
       True
       (and (not (loop3-card-id-member?
                   (loop3-card-id (car-atom $cards))
                   (cdr-atom $cards)))
            (loop3-card-ids-unique? (cdr-atom $cards)))))

;; Each pending obligation carries only its own ancestry. This prunes a genuine
;; cycle without incorrectly suppressing a co-referenced sibling obligation.
(= (loop3-obligation-goal (loop3-obligation $goal $trail)) $goal)
(= (loop3-obligations $goals $trail)
   (if (== $goals ())
       ()
       (cons-atom
         (loop3-obligation (car-atom $goals) $trail)
         (loop3-obligations (cdr-atom $goals) $trail))))

(= (loop3-unresolved-count $hypotheses $facts)
   (if (== $hypotheses ())
       0
       (+ (if (loop3-member?
                 (loop3-obligation-goal (car-atom $hypotheses)) $facts)
               0 1)
          (loop3-unresolved-count (cdr-atom $hypotheses) $facts))))

(= (loop3-node-member? $node $nodes)
   (if (== $nodes ())
       False
       (if (== $node (car-atom $nodes))
           True
           (loop3-node-member? $node (cdr-atom $nodes)))))

(= (loop3-prerequisites-satisfied? $prerequisites $facts)
   (if (== $prerequisites ())
       True
       (and (loop3-member? (car-atom $prerequisites) $facts)
            (loop3-prerequisites-satisfied?
              (cdr-atom $prerequisites) $facts))))

(= (loop3-proof-hard-cap) 64)
(= (loop3-step-hard-cap) 4096)
(= (loop3-candidate-hard-cap) 65536)
(= (loop3-frontier-hard-cap) 4096)
(= (loop3-answer-hard-cap) 256)

(= (loop3-budgets-valid?
      (loop3-budgets $max-proof $max-steps $max-candidates
                     $max-frontier $max-answers))
   (and (> $max-proof 0)
        (and (<= $max-proof (loop3-proof-hard-cap))
          (and (> $max-steps 0)
            (and (<= $max-steps (loop3-step-hard-cap))
              (and (> $max-candidates 0)
                (and (<= $max-candidates (loop3-candidate-hard-cap))
                  (and (> $max-frontier 0)
                    (and (<= $max-frontier (loop3-frontier-hard-cap))
                      (and (> $max-answers 0)
                           (<= $max-answers
                               (loop3-answer-hard-cap))))))))))))

;; ----------------------------------------------------------------------------
;; 2. Backward-via-forward expansion
;; ----------------------------------------------------------------------------

;; Each matching admitted card emits a new hypothetical node. Expansion is an
;; explicit accumulator so the projected frontier is checked BEFORE a node is
;; materialized. Exact-node dedup preserves distinct proof plans while removing
;; genuinely duplicate work.
(= (loop3-expand-cards-acc
      $goal $goal-trail $remaining-hypotheses $proof $proof-size
      $cards $admitted-card-ids $facts $max-proof
      $candidate-count $max-candidates
      $remaining-frontier $max-frontier $nodes-reversed $pruned)
   (let $current-frontier-size
         (+ (size-atom $remaining-frontier) (size-atom $nodes-reversed))
     (if (== $cards ())
         (loop3-expansion
           (loop3-reverse $nodes-reversed)
           $candidate-count $pruned ok $current-frontier-size)
         (if (>= $candidate-count $max-candidates)
             (loop3-expansion
               (loop3-reverse $nodes-reversed)
               $candidate-count $pruned candidate-limit
               $current-frontier-size)
             (let* (($card (car-atom $cards))
                    ($next-count (+ $candidate-count 1)))
               (if (and (== (loop3-card-output $card) $goal)
                        (loop3-card-admitted? $card $admitted-card-ids))
                   (let* (($new-size (+ $proof-size 1))
                          ($new-trail (cons-atom $goal $goal-trail))
                          ($new-hypotheses
                            (loop3-append
                              (loop3-obligations
                                (loop3-reverse
                                  (loop3-card-prerequisites $card))
                                $new-trail)
                              $remaining-hypotheses))
                          ($remaining-proof (- $max-proof $new-size))
                          ($feasible
                            (and (<= $new-size $max-proof)
                                 (<= (loop3-unresolved-count
                                       $new-hypotheses $facts)
                                     $remaining-proof)))
                          ($new-node
                            (loop3-node
                              $new-hypotheses
                              (cons-atom (loop3-card-id $card) $proof)
                              $new-size)))
                     (if (not $feasible)
                         (loop3-expand-cards-acc
                           $goal $goal-trail $remaining-hypotheses
                           $proof $proof-size (cdr-atom $cards)
                           $admitted-card-ids $facts $max-proof
                           $next-count $max-candidates
                           $remaining-frontier $max-frontier
                           $nodes-reversed (+ $pruned 1))
                         (if (or (loop3-node-member?
                                   $new-node $nodes-reversed)
                                 (loop3-node-member?
                                   $new-node $remaining-frontier))
                             (loop3-expand-cards-acc
                               $goal $goal-trail $remaining-hypotheses
                               $proof $proof-size (cdr-atom $cards)
                               $admitted-card-ids $facts $max-proof
                               $next-count $max-candidates
                               $remaining-frontier $max-frontier
                               $nodes-reversed (+ $pruned 1))
                             (if (>= $current-frontier-size $max-frontier)
                                 (loop3-expansion
                                   (loop3-reverse $nodes-reversed)
                                   $next-count $pruned frontier-limit
                                   $current-frontier-size)
                                 (loop3-expand-cards-acc
                                   $goal $goal-trail $remaining-hypotheses
                                   $proof $proof-size (cdr-atom $cards)
                                   $admitted-card-ids $facts $max-proof
                                   $next-count $max-candidates
                                   $remaining-frontier $max-frontier
                                   (cons-atom $new-node $nodes-reversed)
                                   $pruned)))))
                   (loop3-expand-cards-acc
                     $goal $goal-trail $remaining-hypotheses
                     $proof $proof-size (cdr-atom $cards)
                     $admitted-card-ids $facts $max-proof
                     $next-count $max-candidates
                     $remaining-frontier $max-frontier
                     $nodes-reversed $pruned)))))))

(= (loop3-expand-cards
      $goal $goal-trail $remaining-hypotheses $proof $proof-size
      $cards $admitted-card-ids $facts $max-proof
      $candidate-count $max-candidates
      $remaining-frontier $max-frontier)
   (loop3-expand-cards-acc
     $goal $goal-trail $remaining-hypotheses $proof $proof-size
     $cards $admitted-card-ids $facts $max-proof
     $candidate-count $max-candidates
     $remaining-frontier $max-frontier () 0))

(= (loop3-search-finish
      $episode-id $input-hash $target $budgets $status
      $answers $steps $candidates $pruned $peak-frontier)
   (loop3-result
     $answers
     (loop3-receipt
       $episode-id $input-hash $target $budgets $status
       $steps $candidates $pruned (size-atom $answers) $peak-frontier
       inspect-simulate)
     inspect-simulate))

;; The engine is an explicit deterministic frontier machine. A node transition
;; is checked before it executes. Inner card inspection is separately metered.
(= (loop3-search
      $episode-id $input-hash $target $facts $cards $admitted-card-ids
      (loop3-budgets $max-proof $max-steps $max-candidates
                     $max-frontier $max-answers)
      $frontier $answers $steps $candidates $pruned $peak-frontier)
   (let $frontier-size (size-atom $frontier)
     (if (> $frontier-size $max-frontier)
         (loop3-search-finish
           $episode-id $input-hash $target
           (loop3-budgets $max-proof $max-steps $max-candidates
                          $max-frontier $max-answers)
           frontier-limit $answers $steps $candidates $pruned
           (max $peak-frontier $frontier-size))
         (if (>= (size-atom $answers) $max-answers)
             (loop3-search-finish
               $episode-id $input-hash $target
               (loop3-budgets $max-proof $max-steps $max-candidates
                              $max-frontier $max-answers)
               answer-limit $answers $steps $candidates $pruned
               (max $peak-frontier $frontier-size))
             (if (== $frontier ())
                 (loop3-search-finish
                   $episode-id $input-hash $target
                   (loop3-budgets $max-proof $max-steps $max-candidates
                                  $max-frontier $max-answers)
                   (if (== $answers ()) no-answer complete)
                   $answers $steps $candidates $pruned
                   (max $peak-frontier $frontier-size))
                 (if (>= $steps $max-steps)
                     (loop3-search-finish
                       $episode-id $input-hash $target
                       (loop3-budgets $max-proof $max-steps $max-candidates
                                      $max-frontier $max-answers)
                       step-limit $answers $steps $candidates $pruned
                       (max $peak-frontier $frontier-size))
                     (let* (((loop3-node
                               $hypotheses $proof $proof-size)
                             (car-atom $frontier))
                            ($remaining-frontier (cdr-atom $frontier))
                            ($next-steps (+ $steps 1))
                            ($next-peak (max $peak-frontier $frontier-size)))
                       (if (== $hypotheses ())
                           (loop3-search
                             $episode-id $input-hash $target $facts $cards
                             $admitted-card-ids
                             (loop3-budgets
                               $max-proof $max-steps $max-candidates
                               $max-frontier $max-answers)
                             $remaining-frontier
                             (loop3-append
                               $answers
                               ((loop3-answer $target $proof $proof-size)))
                             $next-steps $candidates $pruned $next-peak)
                           (let* (((loop3-obligation $goal $goal-trail)
                                   (car-atom $hypotheses))
                                  ($remaining-hypotheses
                                    (cdr-atom $hypotheses)))
                             (if (loop3-member? $goal $facts)
                                 (loop3-search
                                   $episode-id $input-hash $target
                                   $facts $cards $admitted-card-ids
                                   (loop3-budgets
                                     $max-proof $max-steps $max-candidates
                                     $max-frontier $max-answers)
                                   (cons-atom
                                     (loop3-node
                                       $remaining-hypotheses
                                       $proof $proof-size)
                                     $remaining-frontier)
                                   $answers $next-steps $candidates
                                   $pruned $next-peak)
                                 (if (loop3-member? $goal $goal-trail)
                                     (loop3-search
                                       $episode-id $input-hash $target
                                       $facts $cards $admitted-card-ids
                                       (loop3-budgets
                                         $max-proof $max-steps
                                         $max-candidates $max-frontier
                                         $max-answers)
                                       $remaining-frontier $answers
                                       $next-steps $candidates (+ $pruned 1)
                                       $next-peak)
                                     (let (loop3-expansion
                                            $nodes $next-candidates
                                            $new-pruned $expand-status
                                            $expansion-peak)
                                          (loop3-expand-cards
                                            $goal $goal-trail
                                            $remaining-hypotheses
                                            $proof $proof-size $cards
                                            $admitted-card-ids $facts
                                            $max-proof $candidates
                                            $max-candidates
                                            $remaining-frontier $max-frontier)
                                       (let $final-peak
                                             (max $next-peak $expansion-peak)
                                         (if (or
                                               (== $expand-status
                                                   candidate-limit)
                                               (== $expand-status
                                                   frontier-limit))
                                             (loop3-search-finish
                                               $episode-id $input-hash $target
                                               (loop3-budgets
                                                 $max-proof $max-steps
                                                 $max-candidates $max-frontier
                                                 $max-answers)
                                               $expand-status $answers
                                               $next-steps $next-candidates
                                               (+ $pruned $new-pruned)
                                               $final-peak)
                                             (loop3-search
                                               $episode-id $input-hash $target
                                               $facts $cards
                                               $admitted-card-ids
                                               (loop3-budgets
                                                 $max-proof $max-steps
                                                 $max-candidates $max-frontier
                                                 $max-answers)
                                               (loop3-append
                                                 $nodes $remaining-frontier)
                                               $answers $next-steps
                                               $next-candidates
                                               (+ $pruned $new-pruned)
                                               $final-peak)))))))))))))))

(= (loop3-compose
      $episode-id $input-hash $target $facts $cards $admitted-card-ids
      $budgets)
   (if (loop3-budgets-valid? $budgets)
       (if (loop3-card-ids-unique? $cards)
           (loop3-search
             $episode-id $input-hash $target $facts $cards
             $admitted-card-ids $budgets
             ((loop3-node ((loop3-obligation $target ())) () 0))
             () 0 0 0 1)
           (loop3-search-finish
             $episode-id $input-hash $target $budgets invalid-cards
             () 0 0 0 0))
       (loop3-search-finish
         $episode-id $input-hash $target $budgets invalid-budget
         () 0 0 0 0)))

;; ----------------------------------------------------------------------------
;; 3. Independent direct baseline and plan verifier
;; ----------------------------------------------------------------------------

;; This oracle is intentionally structurally independent of the frontier
;; machine. It recursively enumerates every admitted producing card and takes
;; the Cartesian product of prerequisite proof bags. Duplicate plans remain in
;; the bag; a branch-local goal trail prunes only genuine ancestry cycles.
(= (loop3-trusted-merge-one $head-result $tail-results)
   (if (== $tail-results ())
       ()
       (let* (((trusted-plan $head-plan $head-size) $head-result)
              ((trusted-plan $tail-plan $tail-size)
               (car-atom $tail-results)))
         (cons-atom
           (trusted-plan
             (loop3-append $tail-plan $head-plan)
             (+ $head-size $tail-size))
           (loop3-trusted-merge-one
             $head-result (cdr-atom $tail-results))))))

(= (loop3-trusted-combine-heads
      $head-results $remaining-hypotheses
      $facts $cards $admitted-card-ids $remaining-proof $trail)
   (if (== $head-results ())
       ()
       (let (trusted-plan $head-plan $head-size)
             (car-atom $head-results)
         (let $tail-results
               (loop3-trusted-solve-hypotheses
                 $remaining-hypotheses $facts $cards $admitted-card-ids
                 (- $remaining-proof $head-size) $trail)
           (loop3-append
             (loop3-trusted-merge-one
               (trusted-plan $head-plan $head-size) $tail-results)
             (loop3-trusted-combine-heads
               (cdr-atom $head-results) $remaining-hypotheses
               $facts $cards $admitted-card-ids $remaining-proof $trail))))))

(= (loop3-trusted-solve-hypotheses
      $hypotheses $facts $cards $admitted-card-ids $remaining-proof $trail)
   (if (== $hypotheses ())
       ((trusted-plan () 0))
       (if (< $remaining-proof 0)
           ()
           (let $head-results
                 (loop3-trusted-solve-goal
                   (car-atom $hypotheses) $facts $cards $admitted-card-ids
                   $remaining-proof $trail)
             (loop3-trusted-combine-heads
               $head-results (cdr-atom $hypotheses)
               $facts $cards $admitted-card-ids $remaining-proof $trail)))))

(= (loop3-trusted-attach-card $prerequisite-results $card-id)
   (if (== $prerequisite-results ())
       ()
       (let (trusted-plan $plan $size) (car-atom $prerequisite-results)
         (cons-atom
           (trusted-plan
             (loop3-append $plan ($card-id)) (+ $size 1))
           (loop3-trusted-attach-card
             (cdr-atom $prerequisite-results) $card-id)))))

(= (loop3-trusted-solve-cards
      $goal $facts $remaining-cards $all-cards $admitted-card-ids
      $remaining-proof $trail)
   (if (== $remaining-cards ())
       ()
       (let $card (car-atom $remaining-cards)
         (if (and (== (loop3-card-output $card) $goal)
                  (loop3-card-admitted? $card $admitted-card-ids))
             (let $prerequisite-results
                   (loop3-trusted-solve-hypotheses
                     (loop3-reverse (loop3-card-prerequisites $card))
                     $facts $all-cards $admitted-card-ids
                     (- $remaining-proof 1) (cons-atom $goal $trail))
               (loop3-append
                 (loop3-trusted-attach-card
                   $prerequisite-results (loop3-card-id $card))
                 (loop3-trusted-solve-cards
                   $goal $facts (cdr-atom $remaining-cards) $all-cards
                   $admitted-card-ids $remaining-proof $trail)))
             (loop3-trusted-solve-cards
               $goal $facts (cdr-atom $remaining-cards) $all-cards
               $admitted-card-ids $remaining-proof $trail)))))

(= (loop3-trusted-solve-goal
      $goal $facts $cards $admitted-card-ids $remaining-proof $trail)
   (if (loop3-member? $goal $facts)
       ((trusted-plan () 0))
       (if (or (<= $remaining-proof 0) (loop3-member? $goal $trail))
           ()
           (loop3-trusted-solve-cards
             $goal $facts $cards $cards $admitted-card-ids
             $remaining-proof $trail))))

(= (loop3-trusted-wrap-answers $target $plans)
   (if (== $plans ())
       ()
       (let (trusted-plan $plan $size) (car-atom $plans)
         (cons-atom
           (loop3-answer $target $plan $size)
           (loop3-trusted-wrap-answers $target (cdr-atom $plans))))))

(= (loop3-trusted-answer-bag
      $target $facts $cards $admitted-card-ids $max-proof)
   (loop3-trusted-wrap-answers
     $target
     (loop3-trusted-solve-goal
       $target $facts $cards $admitted-card-ids $max-proof ())))

;; Deterministic forward replay validates that every proposed card is admitted,
;; its prerequisites are present, and the supplied target is produced.
(= (loop3-find-card-id $id $cards)
   (if (== $cards ())
       none
       (if (== (loop3-card-id (car-atom $cards)) $id)
           (car-atom $cards)
           (loop3-find-card-id $id (cdr-atom $cards)))))

(= (loop3-verify-plan-steps $plan $facts $cards $admitted-card-ids)
   (if (== $plan ())
       (plan-replay-valid $facts)
       (let $card (loop3-find-card-id (car-atom $plan) $cards)
         (if (== $card none)
             (plan-replay-invalid unknown-card (car-atom $plan))
             (if (not (loop3-card-admitted? $card $admitted-card-ids))
                 (plan-replay-invalid unadmitted-card (car-atom $plan))
                 (if (loop3-prerequisites-satisfied?
                       (loop3-card-prerequisites $card) $facts)
                     (loop3-verify-plan-steps
                       (cdr-atom $plan)
                       (cons-atom (loop3-card-output $card) $facts)
                       $cards $admitted-card-ids)
                     (plan-replay-invalid
                       unmet-prerequisites (car-atom $plan))))))))

(= (loop3-verify-answer
      (loop3-answer $target $plan $proof-size)
      $facts $cards $admitted-card-ids)
   (let $replay
         (loop3-verify-plan-steps
           $plan $facts $cards $admitted-card-ids)
     (if (== (car-atom $replay) plan-replay-valid)
         (let (plan-replay-valid $post-facts) $replay
           (and (== (size-atom $plan) $proof-size)
                (loop3-member? $target $post-facts)))
         False)))

;; ----------------------------------------------------------------------------
;; 4. Deliberately naive forward baseline for the load-bearing paired fixture
;; ----------------------------------------------------------------------------

(= (loop3-first-applicable $cards $facts $admitted-card-ids)
   (if (== $cards ())
       none
       (let $card (car-atom $cards)
         (if (and (loop3-card-admitted? $card $admitted-card-ids)
                  (loop3-prerequisites-satisfied?
                    (loop3-card-prerequisites $card) $facts))
             $card
             (loop3-first-applicable
               (cdr-atom $cards) $facts $admitted-card-ids)))))

(= (loop3-remove-card $id $cards)
   (if (== $cards ())
       ()
       (if (== (loop3-card-id (car-atom $cards)) $id)
           (cdr-atom $cards)
           (cons-atom
             (car-atom $cards)
             (loop3-remove-card $id (cdr-atom $cards))))))

(= (loop3-naive-forward
      $target $facts $cards $admitted-card-ids $remaining-card-fuel
      $applied-reversed)
   (if (loop3-member? $target $facts)
       (naive-reached $target (loop3-reverse $applied-reversed) $facts)
       (if (<= $remaining-card-fuel 0)
           (naive-budget-exhausted
             $target (loop3-reverse $applied-reversed) $facts)
           (let $card
                 (loop3-first-applicable
                   $cards $facts $admitted-card-ids)
             (if (== $card none)
                 (naive-no-progress
                   $target (loop3-reverse $applied-reversed) $facts)
                 (loop3-naive-forward
                   $target
                   (cons-atom (loop3-card-output $card) $facts)
                   (loop3-remove-card (loop3-card-id $card) $cards)
                   $admitted-card-ids (- $remaining-card-fuel 1)
                   (cons-atom
                     (loop3-card-id $card) $applied-reversed)))))))

;; ----------------------------------------------------------------------------
;; 5. Advisory membrane and result accessors
;; ----------------------------------------------------------------------------

(= (loop3-result-answers
      (loop3-result $answers $receipt $authority))
   $answers)
(= (loop3-result-receipt
      (loop3-result $answers $receipt $authority))
   $receipt)
(= (loop3-receipt-status
      (loop3-receipt
        $episode-id $input-hash $target $budgets $status
        $steps $candidates $pruned $answer-count $peak-frontier $authority))
   $status)
(= (loop3-receipt-steps
      (loop3-receipt
        $episode-id $input-hash $target $budgets $status
        $steps $candidates $pruned $answer-count $peak-frontier $authority))
   $steps)
(= (loop3-receipt-candidates
      (loop3-receipt
        $episode-id $input-hash $target $budgets $status
        $steps $candidates $pruned $answer-count $peak-frontier $authority))
   $candidates)
(= (loop3-receipt-pruned
      (loop3-receipt
        $episode-id $input-hash $target $budgets $status
        $steps $candidates $pruned $answer-count $peak-frontier $authority))
   $pruned)
(= (loop3-receipt-answer-count
      (loop3-receipt
        $episode-id $input-hash $target $budgets $status
        $steps $candidates $pruned $answer-count $peak-frontier $authority))
   $answer-count)
(= (loop3-receipt-peak-frontier
      (loop3-receipt
        $episode-id $input-hash $target $budgets $status
        $steps $candidates $pruned $answer-count $peak-frontier $authority))
   $peak-frontier)
(= (loop3-output-authority $result) inspect-simulate)
(= (loop3-can-grant-effect? $result) False)

;; Native resident fixture: the host provides only opaque episode/input
;; coordinates and transports the resulting advisory proof.
(= (resident-goal-composition-v1 $episode-id $input-ref)
   (loop3-compose
     $episode-id $input-ref causal-test-complete (user-prompt-received)
     ((readiness-card context-step context-assembled
        (user-prompt-received) inspect-simulate)
      (readiness-card plan-step causal-test-complete
        (context-assembled) inspect-simulate))
     (context-step plan-step) (loop3-budgets 4 20 20 20 4)))
