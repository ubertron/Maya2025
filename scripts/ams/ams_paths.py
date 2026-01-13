"""Asset Management System Paths

/ProjectRoot(ElysiumProject)
    /SourceArt              <-- all working files (Maya/Substance/etc.)
    /Unity                  <-- the Unity project folder
        /Core               <-- generic systems used across projects
        /Game(Elysium)
            /Assets
            /Packages
            /ProjectSettings
        /ThirdParty
        /Tools

/SourceArt
    /Animations
    /Audio
    /Characters
        /Hero
            /Model
                hero_high.ma
                hero_high.fbx
            /Textures
                hero_color.spp
                hero_normal.spp
            /Exports
                hero_low.fbx
                hero_low_UVs.fbx
                hero_textures/
    /Environments
        /Forest
            /Model
            /Textures
            /Exports
    /FX
    /Materials
    /Props
    /Vehicles

/Unity/Assets/Game
    /Animations
    /Audio
    /Characters
        /Hero
            hero_low.fbx
            hero_diffuse.png
            hero_normal.png
            hero_material.mat
            hero_prefab.prefab
    /Environments
    /FX
    /Materials
    /Props
    /Scenes -- Unity exclusive
    /Textures
    /Vehicles
    /UI -- Unity exclusive
"""
import os
from dotenv import load_dotenv, find_dotenv
from pathlib import Path


load_dotenv(Path(__file__).parents[2] / ".env")

PROJECT_ROOT = Path(os.path.expanduser(os.getenv("PROJECT_ROOT")))
PROJECT_NAME = os.getenv("PROJECT_NAME")

# Unity paths
UNITY = PROJECT_ROOT / "Unity"
CORE = UNITY / "Core"
GAME = UNITY / PROJECT_NAME
THIRD_PARTY = UNITY / "ThirdParty"
TOOLS = UNITY / "Tools"
ASSETS = GAME / "Assets"
PACKAGES = GAME / "Packages"
PROJECT_SETTINGS = GAME / "ProjectSettings"
TEXTURES = ASSETS / "Textures"
ENVIRONMENTS = ASSETS / "Environments"

# Source art paths
SOURCE_ART = PROJECT_ROOT / "SourceArt"
