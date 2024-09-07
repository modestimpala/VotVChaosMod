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
        local Location = {X=40030.254, Y=-39997.305, Z=5990.244}
        local World = UEHelpers:GetWorld()
        local randomFish = StaticFindObject(fishProps[math.random(1, #fishProps)])
        local bigFish = World:SpawnActor(randomFish, Location, {Pitch=0, Yaw=0, Roll=0}, false, nil, nil, false, false)
        bigFish:SetActorScale3D({X=30, Y=30, Z=30})
        bigFish.Speed = 100
        return true
    end
}