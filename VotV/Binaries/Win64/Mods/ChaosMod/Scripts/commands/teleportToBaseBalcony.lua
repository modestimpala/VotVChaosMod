local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local teleLoc =  {X=-2.197, Y=699.579, Z=6651.074}

        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local World = Pawn:GetWorld()
        local Location = teleLoc
        local Rotation = {Pitch=0.000, Yaw=-0.671, Roll=0.000}
        local fOut = {}
        local mainGamemode_C = FindFirstOf("mainGamemode_C")
        mainGamemode_C.backroomsEnabled = false
        Pawn:K2_SetActorLocation(Location, false, fOut, false)
        ExecuteWithDelay(1000, function()
            mainGamemode_C.backroomsEnabled = true
        end)
    end
}