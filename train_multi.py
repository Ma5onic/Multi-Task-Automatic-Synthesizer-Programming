#import needed modules
import numpy as np
import os
import tensorflow as tf
from tensorflow.keras import losses
import model
import sys
import Experiments.metrics as metrics
import argparse

parser = argparse.ArgumentParser(description='Training parameters')
parser.add_argument('--data-dir', '-d', dest='data_dir', default='npy_data',
                    help='Directory for traing, test, and validation data')
parser.add_argument('--latent-size', '-l', dest='latent_size', type=int, default=64,
                    help='Latent dimmension size')
args = parser.parse_args()

def main():

    # #load in data
    # spec_data = np.load("/vast/df2322/asp_data/all_data_mels.npy",allow_pickle=True)
    # serum_params = np.load("/vast/df2322/asp_data/all_data_serum_params.npy",allow_pickle=True)
    # serum_masks = np.load("/vast/df2322/asp_data/all_data_serum_masks.npy",allow_pickle=True)
    # diva_params = np.load("/vast/df2322/asp_data/all_data_diva_params.npy",allow_pickle=True)
    # diva_masks = np.load("/vast/df2322/asp_data/all_data_diva_masks.npy",allow_pickle=True)
    # tyrell_params = np.load("/vast/df2322/asp_data/all_data_tyrell_params.npy",allow_pickle=True)
    # tyrell_masks = np.load("/vast/df2322/asp_data/all_data_tyrell_masks.npy",allow_pickle=True)

    # m_size = len(spec_data)

    #create splits for training validation and test data
    # all_data_indices = np.random.choice(m_size,m_size,replace=False)
    # train_indices = all_data_indices[:m_size - m_size//5]
    # valid_indices = all_data_indices[m_size - m_size//5: m_size - m_size//10]
    # test_indices = all_data_indices[m_size - m_size//10:]

    train_spec_data = np.load(args.data_dir + "/train_mels.npy",allow_pickle=True)
    train_serum_params = np.load(args.data_dir + "/train_serum_params.npy",allow_pickle=True)
    train_serum_masks = np.load(args.data_dir + "/train_serum_mask.npy",allow_pickle=True)
    train_diva_params = np.load(args.data_dir + "/train_diva_params.npy",allow_pickle=True)
    train_diva_masks = np.load(args.data_dir + "/train_diva_mask.npy",allow_pickle=True)
    train_tyrell_params = np.load(args.data_dir + "/train_tyrell_params.npy",allow_pickle=True)
    train_tyrell_masks = np.load(args.data_dir + "/train_tyrell_mask.npy",allow_pickle=True)

    valid_spec_data = np.load(args.data_dir + "/valid_mels.npy",allow_pickle=True)
    valid_serum_params = np.load(args.data_dir + "/valid_serum_params.npy",allow_pickle=True)
    valid_serum_masks = np.load(args.data_dir + "/valid_serum_mask.npy",allow_pickle=True)
    valid_diva_params = np.load(args.data_dir + "/valid_diva_params.npy",allow_pickle=True)
    valid_diva_masks = np.load(args.data_dir + "/valid_diva_mask.npy",allow_pickle=True)
    valid_tyrell_params = np.load(args.data_dir + "/valid_tyrell_params.npy",allow_pickle=True)
    valid_tyrell_masks = np.load(args.data_dir + "/valid_tyrell_mask.npy",allow_pickle=True)

    test_spec_data = np.load(args.data_dir + "/test_mels.npy",allow_pickle=True)
    test_serum_params = np.load(args.data_dir + "/test_serum_params.npy",allow_pickle=True)
    test_serum_masks = np.load(args.data_dir + "/test_serum_mask.npy",allow_pickle=True)
    test_diva_params = np.load(args.data_dir + "/test_diva_params.npy",allow_pickle=True)
    test_diva_masks = np.load(args.data_dir + "/test_diva_mask.npy",allow_pickle=True)
    test_tyrell_params = np.load(args.data_dir + "/test_tyrell_params.npy",allow_pickle=True)
    test_tyrell_masks = np.load(args.data_dir + "/test_tyrell_mask.npy",allow_pickle=True)

    m_size = len(train_spec_data)

    # np.save("/vast/df2322/asp_data/multi/test_spec",test_spec_data)
    # np.save("/vast/df2322/asp_data/multi/test_serum_params",test_serum_params)
    # np.save("/vast/df2322/asp_data/multi/test_serum_masks",test_serum_masks)
    # np.save("/vast/df2322/asp_data/multi/test_diva_params",test_diva_params)
    # np.save("/vast/df2322/asp_data/multi/test_diva_masks",test_diva_masks)
    # np.save("/vast/df2322/asp_data/multi/test_tyrell_params",test_tyrell_params)
    # np.save("/vast/df2322/asp_data/multi/test_tyrell_masks",test_tyrell_masks)
    


    print(train_spec_data.shape)
    print(train_serum_params.shape)
    print(train_serum_masks.shape)
    print(train_diva_params.shape)
    print(train_diva_masks.shape)
    print(train_tyrell_params.shape)
    print(train_tyrell_masks.shape)


    
    print(m_size)
    #parameter input for dynamic filters
    v_dims = 4

    #batch_size
    batch_size = 32

    #number of batches in one epoch
    batches_epoch = m_size // batch_size

    print(batches_epoch)

    #warmup amount
    warmup_it = 100*batches_epoch

    #list GPUs that tensor flow can use
    physical_devices = tf.config.list_physical_devices('GPU')
    print("Num GPUs:", len(physical_devices))

    #define shapes
    l_dim = args.latent_size
    i_dim = (1, 128, 431, 1)

    #make directory to save model if not already made
    if not os.path.isdir("saved_models/vae_multi_" + str(l_dim)):
        os.makedirs("saved_models/vae_multi_" + str(l_dim))

    # Include the epoch in the file name (uses `str.format`)
    checkpoint_path = "saved_models/vae_multi_" + str(l_dim) + "/cp-{epoch:04d}.ckpt"

    #epoch size
    epochs= 500

    #save freq is every 100 epochs
    save_freq = batches_epoch*100

    # Create a callback that saves the model's weights every 50 epochs
    cp_callback = tf.keras.callbacks.ModelCheckpoint(
        filepath=checkpoint_path,
        verbose=1,
        save_weights_only=True,
        save_freq=save_freq)

    #create model
    m = model.vae_multi(l_dim, i_dim, train_serum_params.shape[-1], train_diva_params.shape[-1], train_tyrell_params.shape[-1], model.optimizer, warmup_it)

    #view summary of model
    m.summary()

    #compile model
    m.compile(optimizer=model.optimizer, loss=losses.MeanSquaredError())

    #update learning rate
    m.optimizer.lr.assign(1e-4)

    #train model
    m.fit([train_spec_data, train_serum_masks, train_diva_masks,train_tyrell_masks],[train_spec_data, train_serum_params, train_diva_params, train_tyrell_params], epochs=epochs, batch_size=batch_size, callbacks=[cp_callback])

    #print evaluation on test set
    loss, loss1,loss2,loss3,loss4 = m.evaluate([test_spec_data, test_serum_masks,test_diva_masks,test_tyrell_masks],[test_spec_data, test_serum_params,test_diva_params, test_tyrell_params],2)
    print("model loss = " + str(loss) + "\n model spectrogram loss = "+ str(loss1) + "\n model synth_param loss = "+ str(loss2))

if __name__ == "__main__":
    main()