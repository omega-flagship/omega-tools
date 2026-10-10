;; New, synthetic snapshot example inspired by the Home Assistant ancestry.
;; No bridge, network, actuator, state write or automatic observation.
(= (tools-habitat-filter $entries $room)
   (if (== $entries ()) ()
       (let $entry (car-atom $entries)
         (if (== (tools-habitat-entry-room $entry) $room)
             (cons-atom $entry (tools-habitat-filter (cdr-atom $entries) $room))
             (tools-habitat-filter (cdr-atom $entries) $room)))))
(= (tools-habitat-entry-room (HabitatObservationV1 $device $room $state)) $room)
(= (tools-habitat-room (HabitatSnapshotV1 $revision $provenance $entries) $room)
   (HabitatRoomViewV1 $revision $provenance $room
     (tools-habitat-filter $entries $room) authority-none))
(= (tools-habitat-can-grant-effect? $value) False)
