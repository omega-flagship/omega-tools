(= (tools-intent-bind $call-id $episode $state) (ToolsSampleResultV1 living-intent (tools-living-intent--living-intent-bind-call $call-id $episode $state) inspect-simulate authority-none))
(= (tools-intent-return $binding $state) (ToolsSampleResultV1 living-intent (tools-living-intent--living-intent-admit-contribution $binding $state) inspect-simulate authority-none))
