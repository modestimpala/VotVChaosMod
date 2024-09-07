local UEHelpers = require("UEHelpers")  -- Load UEHelpers

return {
    execute = function()
        local madness = StaticFindObject("/Game/objects/misc/madnessCombatMaster.madnessCombatMaster_C")
        local World = UEHelpers:GetWorld()
        local spawned = World:SpawnActor(madness, {X=0, Y=0, Z=0}, {Pitch=0, Yaw=0, Roll=0}, false, nil, nil, false, false)
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local Location = Pawn:K2_GetActorLocation()
        local Rotation = Pawn:K2_GetActorRotation()
        local autoshotgun_C = StaticFindObject("/Game/objects/prop_funGun_autoshotgun.prop_funGun_autoshotgun_C")
        local autoshotgun = World:SpawnActor(autoshotgun_C, Location, Rotation, false, nil, nil, false, false)
        -- Pawn:makeLookAt(autoshotgun:K2_GetActorLocation(), {X=Location.X, Y=Location.Y, Z=Location.Z + 80})
        autoshotgun.LifeSpan = 90
        ExecuteWithDelay(90000, function()
            local ui = FindFirstOf("umg_madnessCombat_C")
            ui:RemoveFromViewport()
            spawned:K2_DestroyActor()
            Pawn:forceDrop()
            ExecuteWithDelay(500, function()
                local shotty = FindAllOf("prop_funGun_autoshotgun_C")
                for _, shotgun in pairs(shotty) do
                    shotgun:K2_DestroyActor()
                end
            end)
            local grunts = FindAllOf("prop_grunt_C")
            for _, grunt in pairs(grunts) do
                grunt:K2_DestroyActor()
            end
        end)
        return true
    end
}