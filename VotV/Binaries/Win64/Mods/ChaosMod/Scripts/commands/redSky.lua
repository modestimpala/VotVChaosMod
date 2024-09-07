local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local redSkyEvent = StaticFindObject("/Game/objects/redSkyEvent.redSkyEvent_C")
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local World = Pawn:GetWorld()
        local Location = {X = 0, Y = 0, Z = 0}
        local Rotation = {Pitch = 0, Yaw = 0, Roll = 0}
        if redSkyEvent:IsValid() then
            local spawnedRedSkyEvent = World:SpawnActor(redSkyEvent, Location, Rotation, false, nil, nil, false, false)
            spawnedRedSkyEvent:set(true)
            spawnedRedSkyEvent.isred = true
            return true
        end
        return false
    end
}