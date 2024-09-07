local UEHelpers = require("UEHelpers")  -- Load UEHelpers

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local obj_C = StaticFindObject("/Game/objects/prop_dingus.prop_dingus_C")
        local Location = Pawn:K2_GetActorLocation()
        local Rotation = Pawn:K2_GetActorRotation()
        local World = Pawn:GetWorld()
        local obj = World:SpawnActor(obj_C, Location, Rotation, false, nil, nil, false, false)
        obj:ReceiveBeginPlay()
        local endTime = os.time() + 7
        LoopAsync(120, function()
            if os.time() > endTime then
                return true
            end
            obj:playerHandUse_RMB(Pawn)
            return false
        end)
        return true
    end
}