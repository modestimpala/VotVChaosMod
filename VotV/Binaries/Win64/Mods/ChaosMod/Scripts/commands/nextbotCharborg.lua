local UEHelpers = require("UEHelpers")  -- Load UEHelpers

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local World = Pawn:GetWorld()
        local Location = Pawn:K2_GetActorLocation()
        local Rotation = Pawn:K2_GetActorRotation()

        local navSystem = FindFirstOf("NavigationSystemV1")
        if navSystem:IsValid() then
            print ("Found NavigationSystemV1")
        else
            print("Failed to find NavigationSystemV1")
        end
        local fOut = {}
        local bFoundRandomLocation = navSystem:K2_GetRandomReachablePointInRadius(World, Location, fOut, 5000, nil, nil)
        if bFoundRandomLocation then
            print("Found random location: {X=" .. fOut.X .. ", Y=" .. fOut.Y .. ", Z=" .. fOut.Z .. "}")
            local lib_C = StaticFindObject("/Game/Mods/ChaosMod/Assets/nextbot_callingCharborg.nextbot_callingCharborg_C")
            local lib = World:SpawnActor(lib_C, fOut, {Pitch=0, Yaw=0, Roll=0}, false, nil, nil, false, false)

            lib:PostBeginPlay()
        else
            print("Failed to find random location")
        end
    end
}