local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local World = UEHelpers:GetWorld()
        local find = FindAllOf("computerJumpscare_C")
        if find ~= nil then
            for _, obj in pairs(find) do
                if obj:IsValid() then
                    obj:K2_DestroyActor()
                end
            end
        end
        

        local obj_C = StaticFindObject("/Game/Mods/ChaosMod/Assets/Actors/Effects/computerJumpscare.computerJumpscare_C")
        local obj = World:SpawnActor(obj_C, {X=0, Y=0, Z=0}, {Pitch=0, Yaw=0, Roll=0}, false, nil, nil, false, false)
    
        return true
    end
}