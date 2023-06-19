import json
import os
import shutil
import xml.etree.ElementTree as ET

dataset_dirs = "D:/NNP/pidray/"
dataset_annot = 'annotations/xray_test_easy.json'
dataset_dir = "D:/NNP/pidray/easy/"
sorted_dataset_dir = "D:/NNP/pidray_sorted2/"

def get_category_by_id(categs, id):
    for cat in categs:
        if cat['id'] == id:
            return cat['name']
    return None

with open(dataset_dirs+dataset_annot,'r') as xray_easy:
    x_e = json.load(xray_easy)

    categories = x_e['categories']
    # for cat in categories:
    #     os.mkdir(sorted_dataset_dir+cat['name']+"/")
    # print(categories)

    images = x_e['images']
    annots = x_e['annotations']
    if not (os.path.isdir("D:/NNP/pidray_train_sorted/")):
        os.mkdir(sorted_dataset_dir)
    # print(get_category_by_id(categories,1))
    # print(json.dumps(categories, indent=4))
    print(len(images))
    for j in range(len(images)):
        # if not j == 21029:
        #     continue
        im = [i for i in images if i['id'] == j][0]
        annot = [i for i in annots if i['image_id'] == j]
        # print(annot)
        # print(annot['category_id'])
        # if (annot['category_id'] == ):
        flag = 0
        new_annot = []
        for object in annot:
            if object['category_id'] == 7 or object['category_id'] == 8 or object['category_id'] == 11:
                new_annot.append(object)
                flag = 1
        annot = new_annot
        if flag == 0:
        #     print(new_annot)
        #     break
            continue

        file_name = im['file_name'].split('.png')[0] + ".xml"
        old_im_path = dataset_dir + im['file_name']
        new_im_path = sorted_dataset_dir + im['file_name']
        new_img_xml_path = sorted_dataset_dir + file_name

        # print(old_im_path, new_im_path, new_img_xml_path)
        # break
        shutil.move(old_im_path, new_im_path)
        with open(new_img_xml_path, 'w') as xml_doc:
            root = ET.Element('annotation')
            folder_tag = ET.SubElement(root, 'folder')
            folder_tag.text = sorted_dataset_dir #get_category_by_id(categories, annot['category_id'])
            file_name_tag = ET.SubElement(root, 'filename')
            file_name_tag.text = im['file_name']
            path_tag = ET.SubElement(root, 'path')
            path_tag.text = new_im_path

            source_tag = ET.SubElement(root, 'source')
            database_tag = ET.SubElement(source_tag, 'database')
            database_tag.text = 'Unknown'

            size_tag = ET.SubElement(root, 'size')
            width_tag = ET.SubElement(size_tag, 'width')
            width_tag.text = str(im['width'])
            height_tag = ET.SubElement(size_tag, 'height')
            height_tag.text = str(im['height'])
            depth_tag = ET.SubElement(size_tag, 'depth')
            depth_tag.text = '3'

            segmented_tag = ET.SubElement(root, 'segmented')
            segmented_tag.text = '0'

            for object in annot:
                object_tag = ET.SubElement(root, 'object')
                name_tag = ET.SubElement(object_tag, 'name')
                name_tag.text = get_category_by_id(categories, object['category_id'])
                pose_tag = ET.SubElement(object_tag, 'pose')
                pose_tag.text = 'Unspecified'
                truncated_tag = ET.SubElement(object_tag, 'truncated')
                truncated_tag.text = '0'
                difficult_tag = ET.SubElement(object_tag, 'difficult')
                difficult_tag.text = '0'

                bndbox_tag = ET.SubElement(object_tag, 'bndbox')
                xmin_tag = ET.SubElement(bndbox_tag, 'xmin')
                xmin_tag.text = str(int(object['bbox'][0]))
                ymin_tag = ET.SubElement(bndbox_tag, 'ymin')
                ymin_tag.text = str(int(object['bbox'][1]))
                xmax_tag = ET.SubElement(bndbox_tag, 'xmax')
                xmax_tag.text = str(int(object['bbox'][0]) + int(object['bbox'][2]))
                ymax_tag = ET.SubElement(bndbox_tag, 'ymax')
                ymax_tag.text = str(int(object['bbox'][1]) + int(object['bbox'][3]))

            xml_doc.write(ET.tostring(root, encoding="unicode"))
            xml_doc.close()
        # break
    # for anotations in x_e['anotations']:
    #     i = i + 1
    #     print(json.dumps(anotations['category_id'], indent=4) + '\n' + json.dumps(anotations['bbox'], indent=4))
    #     if (i == 10):
    #         break

