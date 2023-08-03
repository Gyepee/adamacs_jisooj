# Helper functions for post-hoc deconvolved event filtering

import numpy as np
from matplotlib import pyplot as plt


# Ignore numpy warnings
np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning) 
np.warnings.filterwarnings('ignore', category=RuntimeWarning)


class FilterEvents:
    '''
    Deconvolved spikes - filtering methods 
    This method receives an array of raw, deconvolved events and returns a dictionary
    with
    
    -  filtered_events : np.array : Copy of original array, all events below threshold zeroed
    -  filtered_events_count : Number of datapoints remaining after filtering 
    -  event_threshold : float : Threshold used to filter the array (if a global cutoff was used)
                                Note: This can be used in different ways, either as threshold 
                                for events or for signal 
    -  method_name : str : Name of event filtering method
    -  mask_events : np.array : boolean array in length of original events array where True indicates kept events
    '''

    def __init__(self, events):
        self.events = events.copy()
    

    @staticmethod
    def __robust_std(values):
        '''
        Compute the median absolute deviation assuming normally
        distributed data. This is a robust statistic.
        See https://github.com/AllenInstitute/ophys_etl_pipelines/blob/main/src/ophys_etl/utils/traces.py
        Parameters
        ----------
        values: np.ndarray
                A numeric, 1d numpy array
        Returns
        -------
        float:
                A robust estimation of standard deviation.
        Notes
        -----
        If `values` is an empty array or contains any NaNs, will return NaN.
        '''
        mad = np.median(np.abs(values - np.median(values)))
        return 1.4826 * mad


    ###### METHODS #####################################################################################################

    def basic(self,
              cutoff_std
              ):
        '''
        GLOBAL method
        Basic filtering method: Mean + global standard deviation 
        Calculate event filter threshold based on standard deviations over the mean.
        
        Parameters
        ----------
        cutoff_std: float
                   Number of standard deviations over mean for a calcium event to be considered significant
        
        Returns
        -------
        event_dict: dict
        '''
        method_name = 'basic'

        # Sanity checks
        assert isinstance(cutoff_std, float), f'cutoff_std ({cutoff_std}) must be of type float'
        assert cutoff_std > 0, f'{cutoff_std}' f'cutoff_std ({cutoff_std}) must be > 0'

        events_greater0 = self.events[self.events > 0]
        if len(events_greater0) == 0:
            event_threshold = 1  # make sure threshold is higher than zero ;)
        else:
            event_threshold = np.mean(events_greater0) + (cutoff_std * np.std(events_greater0))

        below_thresh = self.events <= event_threshold
        # The below_thresh array is true for areas that will be DISCARDED
        self.events[below_thresh] = 0

        event_dict = {
            'filtered_events'       : self.events,
            'filtered_events_count' : np.sum(self.events>0),
            'event_threshold'      : event_threshold,
            'method_name'          : method_name,
            'mask_events'          : np.logical_not(below_thresh),
        }

        return event_dict

    def robust(self,
               cutoff_std
               ):
        '''
        GLOBAL method
        Similar to method "basic" but with robust estimate of standard deviation.

        Parameters
        ----------
        cutoff_std: float
                    Number of standard deviations over mean for a calcium event to be considered significant
        
        Returns
        -------
        event_dict: dict


        '''

        method_name = 'robust'

        # Sanity checks
        assert isinstance(cutoff_std, float), f'cutoff_std ({cutoff_std}) must be of type float'
        assert cutoff_std > 0, f'{cutoff_std}' f'cutoff_std ({cutoff_std}) must be > 0'

        events_greater0 = self.events[self.events > 0]
        if len(events_greater0) == 0:
            event_threshold = 1  # make sure threshold is higher than zero ;)
        else:
            std = self.__robust_std(events_greater0)
            event_threshold = np.mean(events_greater0) + (cutoff_std * std)

        below_thresh = self.events <= event_threshold
        # The below_thresh array is true for areas that will be DISCARDED
        self.events[below_thresh] = 0

        event_dict = {
            'filtered_events'       : self.events,
            'filtered_events_count' : np.sum(self.events>0),
            'event_threshold'      : event_threshold,
            'method_name'          : method_name,
            'mask_events'          : np.logical_not(below_thresh),
        }

        return event_dict

    def transients(self, 
                   df_f, 
                   mask_baseline, 
                   framerate, 
                   cutoff_std,
                   min_transient_length, 
                   prepended_length=0.4,
                   plot=False,
                   plot_xlim=None,
                   ):
        '''
        GLOBAL method

        Filter significant DeltaF/F transients first and use the extracted mask to filter deconvolved spikes.
        A period of time is defined as a significant transient when its amplitude
        exceeds the standard deviation of baseline DeltaF/F by std * cutoff_std, 
        for a minimum duration of min_transient_length.

        
        Parameters
        ----------
        df_f :               np.ndarray
                             Delta F/F
        mask_baseline :      np.ndarray
                             Boolean array of the same length as df_f. True where baseline.
        framerate :          float
                             Imaging frame rate. Used to convert input in seconds to sample count
        cutoff_std :         float
                             Number of standard deviations for a calcium transient to be considered significant
        min_transient_length:float
                             Minimum number of consecutive timepoints in seconds above threshold for a transient
                             to be considered significant
        prepended_length :   float
                             Number of prepended timepoints in seconds for significant transients
                             Default : 0.4
                             I.e. 0.4 seconds worth of data will be added before the detected start of a transient.
                             This is to compensate for the slow rise time of calcium concentration within the cell. 
        plot:                boolean
                             True - generate figure
        plot_xlim:           2-tuple
                             X axis min and max 
        Returns
        -------
        event_dict : dict    
        
        
        References
        ----------
        Low, Gu and Tank, PNAS (2014) 10.1073/pnas.1421753111 
        Gauthier and Tank, Cell (2018) 10.1016/j.neuron.2018.06.008 

        '''

        method_name = 'transients'

        # Input checks
        assert len(df_f) == len(mask_baseline), 'Lenght of delta F/F signal differs from baseline mask length'
        assert np.sum(mask_baseline), 'No baseline points were found for this cell'
        assert cutoff_std > 0, f'{cutoff_std}' f'cutoff_std ({cutoff_std}) must be > 0'
        assert min_transient_length > 0, f'{min_transient_length}' f'min_transient_length ({min_transient_length}) must be > 0'
        assert prepended_length > 0, f'prepended_length ({prepended_length}) must be > 0'

        ############## BASELINE EXTRACTION AND FCORR CORRECTION ########################################################

        # Convert input from seconds to samples
        min_transient_samples= int(np.round(min_transient_length * framerate))
        prepended_samples    = int(np.round(prepended_length * framerate))
        transient_std = cutoff_std
        
        ############## FILTER SIGNIFICANT TRANSIENTS ####################################################################
        std_df_f_baseline = np.nanstd(df_f[mask_baseline]) # There should be no NaNs, but be safe
        transient_threshold = std_df_f_baseline * transient_std
        transient_mask = df_f > transient_threshold

        significant_transient_mask = np.zeros_like(transient_mask)
        # Remove samples that are individually high but _not_ part of a consecutive group >= min_transient_samples
        counter = 0
        in_transient = False
        sufficiently_long = False
        for i, el in enumerate(transient_mask):
            # Iterate through the array
            if not in_transient:
                # Not already processing something
                if el:
                    # Start tracking a new potential transient
                    in_transient = True
                    counter = 1
            else:
                # Already processing a potential transient
                if el:
                    # continue tracking it
                    counter +=1
                    if counter >= min_transient_samples:
                        # This passes muster, mark it to be included at the end
                        sufficiently_long = True

                else:
                    # Come to the end of the transient: mark it as significant (if
                    # necessary) and reset for the next potential
                    # Also extend at the beginning by "prepended_samples"
                    if sufficiently_long:
                        significant_transient_mask[i-counter-prepended_samples:i] = True
                    counter = 0
                    in_transient = False
                    sufficiently_long = False


        # The significant_transient_mask is TRUE when spikes SHALL BE KEPT
        self.events[np.logical_not(significant_transient_mask)] = 0

        event_dict = {
            'filtered_events'        : self.events,
            'filtered_events_count'  : np.sum(self.events>0),
            'event_threshold'       : transient_threshold,  
            'method_name'           : method_name,
            'mask_events'           : significant_transient_mask,
        }

        ############## OPTIONAL: PLOT ##################################################################################
        # Generate optional plot to show the extraction of significant transients
        if plot:
            plt.figure(figsize=(12,3))
            p0, = plt.plot(df_f, color='#000', alpha=.4, label='dF/F')
            p1 = plt.axhline(y= transient_threshold, ls=':', color='red',label='Cutoff')

            masked_fcorr4plot = df_f.copy()
            masked_fcorr4plot[~significant_transient_mask] = np.nan
            
            p2, = plt.plot(masked_fcorr4plot, color='#ff0000', alpha=.6, label='Significant transients')
            
            if plot_xlim is not None: 
                plt.xlim(plot_xlim)
            else:
                plt.xlim(0,len(df_f))
            
            plt.axhline(y=0, color='#333', ls='--')
            
            plt.legend()
            plt.legend(handles=[p0, p1, p2], title='', bbox_to_anchor=(1.01, 1), loc='upper left')
            plt.show()
            
        return event_dict