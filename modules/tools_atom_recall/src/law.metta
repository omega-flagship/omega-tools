;; Native exact-symbolic recall over a typed atom-memory candidate pool.
;; Chroma is queried at the grounded retrieval boundary in parallel; both
;; resulting pools are reconciled later by native Focus.

(= (memory-ref-present? $ref $refs)
   (if (== $refs ())
       False
       (if (== $ref (car-atom $refs))
           True
           (memory-ref-present? $ref (cdr-atom $refs)))))

(= (memory-any-key-present? $keys $query-refs)
   (if (== $keys ())
       False
       (if (memory-ref-present? (car-atom $keys) $query-refs)
           True
           (memory-any-key-present? (cdr-atom $keys) $query-refs))))

(= (atom-memory-entry-ref (AtomMemoryEntryV1 $ref $keys)) $ref)
(= (atom-memory-entry-keys (AtomMemoryEntryV1 $ref $keys)) $keys)

(= (atom-memory-recall-refs $query-refs $entries)
   (if (== $entries ())
       ()
       (let* (($entry (car-atom $entries))
              ($remaining (cdr-atom $entries))
              ($matches
                (memory-any-key-present?
                  (atom-memory-entry-keys $entry) $query-refs)))
         (if $matches
             (cons-atom
               (atom-memory-entry-ref $entry)
               (atom-memory-recall-refs $query-refs $remaining))
             (atom-memory-recall-refs $query-refs $remaining)))))

(= (atom-memory-recall-v1 $request-id $query-refs $entries)
   (AtomMemoryRecallDecisionV1
     $request-id
     (atom-memory-recall-refs $query-refs $entries)
     authority-none))

(= (memory-recall-can-grant-effect? $decision) False)

;; Recall policy is distinct from the physical adapters. Python serializes raw
;; scalars into these closed carriers; this organ owns acceptance and refusal.
(= (memory-recall-text-equals? $carrier $expected)
   (case $carrier
     (((MemoryRecallTextV1 $actual) (== $actual $expected))
      ($invalid False))))

(= (memory-recall-source-valid? $carrier)
   (or (memory-recall-text-equals? $carrier "atom-memory")
       (or (memory-recall-text-equals? $carrier "chroma-semantic")
           ;; ADDITIVE (checkpoint 2): the derived dynamic memory mirror is a
           ;; candidate SOURCE only -- rediscovery, never truth or authority.
           (memory-recall-text-equals? $carrier "dynamic-memory-mirror"))))

(= (memory-recall-access-valid? $carrier)
   (or (memory-recall-text-equals? $carrier "provider-approved")
       (memory-recall-text-equals? $carrier "local-only")))

(= (memory-recall-loss-valid? $carrier)
   (or (memory-recall-text-equals? $carrier "exact-extract")
       (or (memory-recall-text-equals? $carrier "semantic-summary")
           (memory-recall-text-equals? $carrier "pointer-only"))))

(= (memory-recall-relevance-valid? $carrier)
   (case $carrier
     (((MemoryRecallIntegerV1 $value)
       (and (>= $value 0)
            (and (<= $value 1000) (== (floor-math $value) $value))))
      ($invalid False))))

;; The Chroma adapter carries raw identifier code points; this law, rather
;; than the adapter, owns the [a-z0-9][a-z0-9-]{0,95} measurement boundary.
(= (memory-recall-symbol-first-code? $code)
   (or (and (>= $code 48) (<= $code 57))
       (and (>= $code 97) (<= $code 122))))

(= (memory-recall-symbol-tail-code? $code)
   (or (== $code 45) (memory-recall-symbol-first-code? $code)))

(= (memory-recall-symbol-tail-codes-valid? $codes $remaining)
   (if (== $codes ())
       True
       (if (not (is-expr $codes))
           False
           (if (<= $remaining 0)
               False
               (and (memory-recall-symbol-tail-code? (car-atom $codes))
                    (memory-recall-symbol-tail-codes-valid?
                      (cdr-atom $codes) (- $remaining 1)))))))

(= (memory-recall-identifier-codepoints-valid? $codepoints)
   (case $codepoints
     (((MemoryRecallIdentifierCodepointsV1 $codes)
       (if (or (== $codes ()) (not (is-expr $codes)))
           False
           (and (memory-recall-symbol-first-code? (car-atom $codes))
                (memory-recall-symbol-tail-codes-valid? (cdr-atom $codes) 95))))
      ($invalid False))))

(= (memory-recall-chroma-identifier-valid? $identifier $codepoints)
   (case $identifier
     (((MemoryRecallTextV1 $raw)
       (memory-recall-identifier-codepoints-valid? $codepoints))
      ($invalid False))))

(= (memory-recall-chroma-measurement-policy-v1 $nomination)
   (case $nomination
     (((MemoryRecallChromaMeasurementPolicyNominationV1
         $identifier $codepoints $relevance authority-none)
       (if (not (memory-recall-chroma-identifier-valid? $identifier $codepoints))
           (MemoryRecallChromaMeasurementPolicyRefusalV1
             $identifier $codepoints $relevance identifier-invalid authority-none)
           (if (memory-recall-relevance-valid? $relevance)
               (MemoryRecallChromaMeasurementPolicyDecisionV1
                 $identifier $codepoints $relevance admitted authority-none)
               (MemoryRecallChromaMeasurementPolicyRefusalV1
                 $identifier $codepoints $relevance relevance-invalid authority-none))))
      ($invalid
       (MemoryRecallChromaMeasurementPolicyRefusalV1
         nomination-shape-invalid authority-none)))))

(= (memory-recall-candidate-source-policy-v1 $nomination)
   (case $nomination
     (((MemoryRecallCandidateSourcePolicyNominationV1 $source authority-none)
       (if (memory-recall-source-valid? $source)
           (MemoryRecallCandidateSourcePolicyDecisionV1 $source admitted authority-none)
           (MemoryRecallCandidateSourcePolicyRefusalV1 $source source-type-invalid authority-none)))
      ($invalid
       (MemoryRecallCandidateSourcePolicyRefusalV1 nomination-shape-invalid authority-none)))))

;; Dynamic-mirror hits are a THIRD population whose scores are not calibrated
;; against Atom or adopted Chroma relevance.  Native law owns the only
;; admissible fusion: an AIKR PAGE over the source's own rank order, with an
;; explicit continuation.  Python carries ($count $limit $offset), where $count
;; is how many hits the mirror returned from $offset (it fetches one beyond the
;; limit so the remainder is measurable); it never decides how many survive,
;; nor whether the lane is open.  Omitted hits remain reachable at $next.
(= (memory-recall-dynamic-page-policy-v1 $nomination)
   (case $nomination
     (((MemoryRecallDynamicPageNominationV1 $count $limit $offset authority-none)
       (if (or (< $count 0) (or (< $limit 1) (< $offset 0)))
           (MemoryRecallDynamicPageRefusalV1 $count $limit $offset page-invalid authority-none)
           (let $admit (if (< $count $limit) $count $limit)
             (MemoryRecallDynamicPageDecisionV1 $count $limit $offset
               $admit (+ $offset $admit)
               (if (< $limit $count) open exhausted)
               admitted authority-none))))
      ($invalid
       (MemoryRecallDynamicPageRefusalV1 nomination-shape-invalid authority-none)))))

;; ANN V2 carries a complete measured page plus an opaque cursor. A short or
;; empty page can still have an open search frontier. No already-returned hit
;; is discarded: a response exceeding its requested native quantum refuses.
;; The binding is a digest of the exact request, answered snapshot and reply;
;; it is a physical coordinate, never a semantic execution permit.
(= (memory-recall-dynamic-page-policy-v2 $nomination)
   (case $nomination
     (((MemoryRecallDynamicPageNominationV2 $count $limit $cursor-present
         $measured-remaining $segments-remaining $binding
         approximate-nonexhaustive-segment-window authority-none)
       (if (or (< $count 0)
               (or (< $limit 1)
                   (or (< $limit $count)
                       (or (< $measured-remaining 0) (< $segments-remaining 0)))))
           (MemoryRecallDynamicPageRefusalV2 $binding page-invalid authority-none)
           (let $open (or (< 0 $measured-remaining) (< 0 $segments-remaining))
             (if (== $cursor-present $open)
                 (MemoryRecallDynamicPageDecisionV2 $count $limit $cursor-present
                   $measured-remaining $segments-remaining $binding $count
                   (if $open open exhausted) admitted authority-none)
                 (MemoryRecallDynamicPageRefusalV2 $binding frontier-crossed authority-none)))))
      ($invalid
       (MemoryRecallDynamicPageRefusalV2 nomination-shape-invalid authority-none)))))

(= (memory-recall-candidate-policy-v1 $nomination)
   (case $nomination
     (((MemoryRecallCandidatePolicyNominationV1 $access $loss $relevance authority-none)
       (if (memory-recall-text-equals? $access "private-self")
           (MemoryRecallCandidatePolicyRefusalV1 $access $loss $relevance private-memory-not-eligible authority-none)
           (if (not (memory-recall-access-valid? $access))
               (MemoryRecallCandidatePolicyRefusalV1 $access $loss $relevance access-class-invalid authority-none)
               (if (not (memory-recall-loss-valid? $loss))
                   (MemoryRecallCandidatePolicyRefusalV1 $access $loss $relevance loss-semantics-invalid authority-none)
                   (if (memory-recall-relevance-valid? $relevance)
                       (MemoryRecallCandidatePolicyDecisionV1 $access $loss $relevance admitted authority-none)
                       (MemoryRecallCandidatePolicyRefusalV1 $access $loss $relevance relevance-invalid authority-none))))))
      ($invalid
       (MemoryRecallCandidatePolicyRefusalV1 nomination-shape-invalid authority-none)))))

(= (memory-recall-atom-entry-policy-v1 $nomination)
   (case $nomination
     (((MemoryRecallAtomEntryPolicyNominationV1 $source authority-none)
       (if (memory-recall-text-equals? $source "atom-memory")
           (MemoryRecallAtomEntryPolicyDecisionV1 $source admitted authority-none)
           (MemoryRecallAtomEntryPolicyRefusalV1 $source source-invalid authority-none)))
      ($invalid
       (MemoryRecallAtomEntryPolicyRefusalV1 nomination-shape-invalid authority-none)))))

(= (memory-recall-source-pair-policy-v1 $nomination)
   (case $nomination
     (((MemoryRecallSourcePairPolicyNominationV1 $atom-source $chroma-source authority-none)
       (if (and (memory-recall-text-equals? $atom-source "atom-memory")
                (memory-recall-text-equals? $chroma-source "chroma-semantic"))
           (MemoryRecallSourcePairPolicyDecisionV1 $atom-source $chroma-source admitted authority-none)
           (MemoryRecallSourcePairPolicyRefusalV1 $atom-source $chroma-source source-pair-invalid authority-none)))
      ($invalid
       (MemoryRecallSourcePairPolicyRefusalV1 nomination-shape-invalid authority-none)))))

(= (memory-recall-eligible-source-record $source-ref $eligible)
   (if (== $eligible ())
       none
       (case (car-atom $eligible)
         (((MemoryRecallEligibleAtomV1 $seen-source-ref $access $loss)
           (if (== $source-ref $seen-source-ref)
               (MemoryRecallEligibleAtomV1 $seen-source-ref $access $loss)
               (memory-recall-eligible-source-record
                 $source-ref (cdr-atom $eligible))))
          ($invalid none)))))

(= (memory-recall-chroma-eligibility-join-v1 $nomination)
   (case $nomination
     (((MemoryRecallChromaEligibilityJoinNominationV1
         $source-ref $eligible authority-none)
       (case (memory-recall-eligible-source-record $source-ref $eligible)
         (((MemoryRecallEligibleAtomV1 $matched-source-ref $access $loss)
           (MemoryRecallChromaEligibilityJoinDecisionV1
             $matched-source-ref $access $loss $eligible admitted authority-none))
          (none
           (MemoryRecallChromaEligibilityJoinRefusalV1
             $source-ref $eligible not-eligible authority-none)))))
      ($invalid
       (MemoryRecallChromaEligibilityJoinRefusalV1 nomination-shape-invalid authority-none)))))
