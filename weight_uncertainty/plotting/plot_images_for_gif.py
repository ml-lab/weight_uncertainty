import numpy as np
import matplotlib.pyplot as plt
from os.path import join
from weight_uncertainty import conf
from weight_uncertainty.util.util import maybe_make_dir
from weight_uncertainty.util.load_data import normalize
import subprocess

latex = True  # set to True for latex formatting

mc_type = 'mc_vif'
for mutilation, var_name, _, _ in conf.experiments:
    # Load all our data
    images = np.load('log_risk/%s.%s.im.npy' % (mutilation, mc_type))
    risks = np.load('log_risk/%s.%s.risks.npy' % (mutilation, mc_type))
    mean_risks = np.mean(risks, axis=-1)  # Mean risks are used in the suptitle
    output_dir = f'im/{conf.dataset}/{mutilation}'
    if latex:
        output_dir = join(output_dir, 'latex')
    maybe_make_dir(output_dir)  # Make dir to save images

    # Do some fact checking :)
    num_experiments, num_batch = images.shape[:2]
    assert risks.shape[0] == num_experiments
    assert risks.shape[2] == num_batch

    # Some constants used for plotting
    num_rows = 2
    num_cols = 6
    width_add = 10

    # Centralize the risks, because I have no clue what a 'good' value and what a 'bad' value is
    risks_cent = (risks - np.mean(risks, axis=0)) / (np.std(risks, axis=0) + 1E-9)

    # Values to scale the plotting of entropy
    entropy_min = -1.
    entropy_max = 1.0

    for num_experiment in range(num_experiments):
        f, axarr = plt.subplots(num_rows, num_cols, figsize=(15, 5))

        batch_count = 0
        for num_row in range(num_rows):
            for num_col in range(num_cols):
                # Color indicates correct / incorrect
                color = 'g' if risks[num_experiment, 5, batch_count].astype(np.bool) else 'r'

                im_array = normalize(np.squeeze(images[num_experiment, batch_count]), reverse=True)
                im_width = im_array.shape[0]

                # Get the gray value to indicate uncertainty
                gray_value = (risks_cent[num_experiment, 2, batch_count] - entropy_min) / (
                    entropy_max - entropy_min)  # Transform the range to [0, 1]
                gray_value = np.clip(gray_value, 0.0, 1.0) * 255.  # Scale to 255 for imshow to work

                # Split up code for MNIST (2D) or CIFAR (3D) data set
                if conf.dataset == 'mnist':
                    im_array_wide = np.ones((im_width + width_add*2, im_width + width_add*2)) * gray_value
                    im_array_wide[width_add:width_add+im_width, width_add:width_add+im_width] = im_array

                    axarr[num_row, num_col].imshow(im_array_wide, cmap = 'gray')
                    axarr[num_row, num_col].set_title(f'Entropy{risks[num_experiment, 2, batch_count]:7.3f}',
                                                color=color)
                elif conf.dataset == 'cifar':
                    im_array_wide = np.ones((im_width + width_add * 2, im_width + width_add * 2, 3)) * gray_value
                    im_array_wide[width_add:width_add + im_width, width_add:width_add + im_width] = im_array

                    axarr[num_row, num_col].imshow(im_array_wide.astype(np.uint8), cmap='gray')
                    axarr[num_row, num_col].set_title(f'Entropy{risks[num_experiment, 2, batch_count]:7.3f}',
                                                      color=color)
                else:
                    assert False
                batch_count += 1

        # Matplotlib magic :)
        for axrow in axarr:
            for ax in axrow:
                # We don't need ticklabels for image plotting
                plt.setp(ax.get_xticklabels(), visible=False)
                plt.setp(ax.get_yticklabels(), visible=False)
        f.suptitle('%s %3.3f mean entropy %5.3f' %
                   (var_name, mean_risks[num_experiment, 0], mean_risks[num_experiment, 2]))
        plt.subplots_adjust(wspace=0.1, hspace=0.5)
        name = '%03i.png' % num_experiment if not latex else str(num_experiment)
        plt.savefig(join(output_dir, 'experiment' + name))
        plt.close("all")
        print(f'Mutilation {mutilation} experiment {name}')

    if not latex:
        # Insert command line to make a GIF
        print('Also make GIF')
        subprocess.call(['convert', '-delay', '40', '-loop', '0', '*.png', f'{mutilation}_uncertain.gif'],
                        cwd=output_dir)
