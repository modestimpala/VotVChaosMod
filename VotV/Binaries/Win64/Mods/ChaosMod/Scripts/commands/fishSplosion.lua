local UEHelpers = require("UEHelpers")  -- Load UEHelpers

return {
    execute = function()
        local fishProps = {
            "/Game/objects/prop_fish_1.prop_fish_1_C",
            "/Game/objects/prop_fish_2.prop_fish_2_C",
            "/Game/objects/prop_fish_3.prop_fish_3_C",
            "/Game/objects/prop_fish_4.prop_fish_4_C",
            "/Game/objects/prop_fish_5.prop_fish_5_C",
            "/Game/objects/prop_fish_6.prop_fish_6_C",
            "/Game/objects/prop_fish_7.prop_fish_7_C",
            "/Game/objects/prop_fish_8.prop_fish_8_C",
            "/Game/objects/prop_fish_9.prop_fish_9_C",
            "/Game/objects/prop_fish_10.prop_fish_10_C",
            "/Game/objects/prop_fish_11.prop_fish_11_C",
            "/Game/objects/prop_fish_12.prop_fish_12_C",
            "/Game/objects/prop_fish_13.prop_fish_13_C",
            "/Game/objects/prop_fish_14.prop_fish_14_C"
        }
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local Location = Pawn:K2_GetActorLocation()
        local World = UEHelpers:GetWorld()
        int = 0
        for i = 1, 30 do
            local Rotation = {Pitch=math.random(0, 360), Yaw=math.random(0, 360), Roll=math.random(0, 360)}
            local fish = StaticFindObject(fishProps[math.random(1, #fishProps)])
            local spawned = World:SpawnActor(fish, Location, Rotation, false, nil, nil, false, false)
            spawned.dead = true
        end
    end
}