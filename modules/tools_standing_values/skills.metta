(= (tools-value-transition $request) (ToolsSampleResultV1 standing-values (tools-standing-values--standing-value-transition-v1 $request) inspect-simulate authority-none))
(= (tools-retention-check $covenant $operation) (ToolsSampleResultV1 standing-values (tools-standing-values--retention-guard-operation-v1 $covenant $operation) inspect-simulate authority-none))
