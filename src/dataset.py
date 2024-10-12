from abc import ABC
from typing import Any
from PIL import Image
import glob
import random
import cv2
import numpy as np
import os
import tqdm
from pathlib import Path
import json


class MapGenerator:
    MIN_GROUP_BY_MAP = 0
    MAX_GROUP_BY_MAP = 3

    def __init__(self, base_path, empty_maps_path, stickers_path, classes, p_mobs):
        self.base_path = base_path
        self.empty_maps_path = empty_maps_path
        self.stickers_path = stickers_path
        self.bg_area_folder = f"{base_path}/{empty_maps_path}"
        self.fg_folder = f"{base_path}/{stickers_path}"
        self.classes = classes
        self.p_mobs = p_mobs
        self.label = ""

    def generate_image(self):
        area = self.pick_bg_area()
        empty_map_path = self.pick_empty_map(f"{self.bg_area_folder}/{area}/crop")
        bg_image = BackgroundImage(empty_map_path)
        mobs = self.get_mobs(area, bg_image)
        ressources = self.get_ressources(bg_image)
        return bg_image, mobs, ressources

    def pick_bg_area(self) -> str:
        bg_area_list = glob.glob(f"{self.bg_area_folder}/*")
        area_path = random.choice(bg_area_list)
        return Path(area_path).stem

    def pick_empty_map(self, path) -> str:
        empty_map_list = glob.glob(f"{path}/*")
        empty_map_path = random.choice(empty_map_list)
        return empty_map_path

    def pick_number_of_mobs(self):
        number_of_mobs = np.random.choice(
            np.arange(self.MIN_GROUP_BY_MAP, self.MAX_GROUP_BY_MAP + 1),
            1,
            p=self.p_mobs,
        )[0]
        return number_of_mobs

    def pick_number_of_ressources(self, max_instances):
        number_of_ressources = np.random.choice(
            np.arange(0, max_instances + 1),
            1,
        )[0]
        return number_of_ressources

    def pick_mob(self, mob_list):
        mob = random.choice(mob_list)
        mob_path = self.pick_mob_orientation(mob)
        return mob_path

    def pick_mob_orientation(self, path):
        mob_orien_list = glob.glob(f"{path}/final/*")
        mob_path = random.choice(mob_orien_list)
        return mob_path

    def get_mobs(self, area, bg_image):
        mob_list = glob.glob(f"{self.fg_folder}/mobs/{area}/*")
        if mob_list:
            number_of_mobs = self.pick_number_of_mobs()
            mobs = [
                MobStickerImage(self.pick_mob(mob_list)).pick_x_and_y(bg_image)
                for j in range(number_of_mobs)
            ]
        else:
            mobs = []
        return mobs

    def get_ressources(self, bg_image):
        ressources = {}
        if "ressources" in bg_image.metadata:
            for ressource, ress_dict in bg_image.metadata["ressources"].items():
                ressource_list = glob.glob(
                    f"{self.fg_folder}/ressources/{ressource}/final/*"
                )
                ressource_path = ressource_list[0]
                if "max_instances" in ress_dict:
                    number_of_ressources = self.pick_number_of_ressources(
                        ress_dict["max_instances"]
                    )
                    ressources[ressource] = [
                        RessourceStickerImage(ressource_path).pick_x_and_y(bg_image)
                        for i in range(number_of_ressources)
                    ]
                elif "x" in ress_dict and "y" in ress_dict:
                    ressources[ressource] = []
                    for x, y in zip(ress_dict["x"], ress_dict["y"]):
                        ressources[ressource].append(
                            RessourceStickerImage(ressource_path, tl=(x, y))
                        )
                else:
                    print("Keys don't taken into account")


class ElemImage:
    def __init__(self, path) -> None:
        self.path = Path(path)
        self.img = Image.open(self.path, "r")
        self.width, self.height = self.img.size


class BackgroundImage(ElemImage):
    def __init__(self, path) -> None:
        super().__init__(path=path)
        self.metadata = self.get_metadata()

    def get_metadata(self) -> dict:
        with open(
            self.path.as_posix().replace("crop", "metadata").replace("jpg", "json"), "r"
        ) as file:
            metadata = json.load(file)
        split = self.path.stem.split("_")
        if len(split) == 5:
            (
                metadata["city"],
                metadata["area"],
                metadata["x"],
                metadata["y"],
                metadata["level"],
            ) = split

        elif len(split) == 4:
            (
                metadata["city"],
                metadata["area"],
                metadata["x"],
                metadata["y"],
            ) = split
        else:
            print(f"{split = }")
            raise RuntimeError("Split has not length of 4 or 5.")
        return metadata


class StickerImage(ElemImage):
    def __init__(self, path, tl=(None, None)) -> None:
        super().__init__(path=path)
        self.metadata = self.get_metadata()
        self.tl = tl

    def get_metadata(self):
        pass


class MobStickerImage(StickerImage):
    def __init__(self, path, tl=(None, None)) -> None:
        super().__init__(path, tl)

    def get_metadata(self):
        split = self.path.stem.split("_")
        metadata = {}
        if len(split) == 3:
            metadata["name"], metadata["orientation"], _ = split
        else:
            print(f"{split = }")
            raise RuntimeError("Split has not length of 3 for mob sticker.")
        return metadata

    def pick_x_and_y(self, bg_image: BackgroundImage):
        mask_path = bg_image.path.as_posix().replace("crop", "mask")
        img = Image.open(mask_path).convert("L")
        img_arr = np.array(img)
        white_pix = list(np.argwhere(img_arr == 255))
        if not white_pix:
            self.tl = (None, None)
        else:
            self.tl = random.choice(white_pix)
        return self


class RessourceStickerImage(StickerImage):
    def __init__(self, path, tl=(None, None)) -> None:
        super().__init__(path, tl)

    def get_metadata(self):
        split = self.path.stem.split("_")
        metadata = {}
        if len(split) == 2:
            metadata["name"], _ = split
        else:
            print(f"{split = }")
            raise RuntimeError("Split has not length of 2 for ressource sticker.")
        return metadata

    def pick_x_and_y(self, bg_image: BackgroundImage):
        mask_path = bg_image.path.as_posix().replace("crop", "mask")
        img = Image.open(mask_path).convert("L")
        img_arr = np.array(img)
        white_pix = list(np.argwhere(img_arr == 255))
        if not white_pix:
            not_white_pix = list(np.argwhere(img_arr != 255))
            self.tl = random.choice(not_white_pix)
        else:
            self.tl = random.choice(white_pix)
        return self


class DatasetCreator:
    def __init__(
        self, data_rel_path, train_size, number_of_img, p_mobs, show=False, write=False
    ):
        self.data_rel_path = data_rel_path
        self.train_size = train_size
        self.number_of_img = number_of_img
        self.p_mobs = p_mobs
        self.show = show
        self.write = write

    # Other methods for creating train and validation datasets


if __name__ == "__main__":
    # Configuration
    base_path = "D:/Documents/13_Projet/dlcv4ldb/02_Donnees"
    empty_maps_path = "empty_maps/incarnam"
    stickers_path = "stickers/incarnam"

    classes = [
        # Class names here
    ]

    # Initializing the components
    map_generator = MapGenerator(base_path, empty_maps_path, stickers_path, classes)
    # image_handler = ImageHandler()
    dataset_creator = DatasetCreator(
        "../02_Donnees/datasets", 0.5, 3, [0.1, 0.2, 0.3, 0.4], show=True, write=False
    )

    # Usage of the components for dataset creation
    for img_number in tqdm.tqdm(
        range(dataset_creator.number_of_img), desc="Creating dataset"
    ):
        # Logic for dataset creation using the classes and methods
        pass
