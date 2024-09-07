local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local radioTowerLoc =   {X=6163.530, Y=-37596.008, Z=24303.418}

        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local World = Pawn:GetWorld()
        local Location = radioTowerLoc
        local Rotation = {Pitch=0.000, Yaw=62.138, Roll=0.000}
        local fOut = {}
        local mainGamemode_C = FindFirstOf("mainGamemode_C")
        mainGamemode_C.backroomsEnabled = false
        Pawn:K2_SetActorLocation(Location, false, fOut, false)
        ExecuteWithDelay(1000, function()
            mainGamemode_C.backroomsEnabled = true
        end)
    end
}