local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local cig = StaticFindObject("/Game/objects/cig.cig_C")
        local Location = Pawn:K2_GetActorLocation()
        local Rotation = Pawn:K2_GetActorRotation()
        local World = Pawn:GetWorld()
        local i = 0
        for i = 0, 500 do
            local cig = World:SpawnActor(cig, Location, Rotation, false, nil, nil, false, false)
            Pawn.cig = cig
            cig.lit(true)
            i = i + 1
        end
        local mainGame = FindFirstOf("mainGamemode_C")
        mainGame.Immortal = true
        ExecuteWithDelay(45000, function()
            local cigs = FindAllOf("cig_C")
            for _, cig in pairs(cigs) do
                cig:K2_DestroyActor()
            end

            mainGame.Immortal = false
        end)
        return true
    end
}