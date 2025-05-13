module cmflib

  use iso_c_binding, only : c_null_char, c_char, c_int, c_size_t, c_ptr, c_loc, c_null_ptr

  implicit none
  private

#ifndef C_MAX_STRING
  integer, parameter :: C_MAX_STRING = 256
#endif
  ! Define interfaces to C-routines
  interface
    subroutine cmf_init(mlmd_path, pipeline_name, context_name, execution_name) bind(C)
      use iso_c_binding, only : c_char
      character(kind=c_char), intent(in) :: mlmd_path(*), pipeline_name(*), context_name(*), execution_name(*)
    end subroutine cmf_init
  end interface

  interface
    integer(kind=c_int) function is_cmf_initialized() bind(C)
      use iso_c_binding, only : c_int
    end function is_cmf_initialized
  end interface

  interface
    subroutine log_metric_c(key, dict_keys_ptr, dict_values_ptr, dict_size) bind(C, name="log_metric")
      use iso_c_binding, only : c_char, c_int, c_ptr
      character(kind=c_char),     intent(in) :: key(*)
      type(c_ptr), value,         intent(in) :: dict_keys_ptr
      type(c_ptr), value,         intent(in) :: dict_values_ptr
      integer(kind=c_int), value, intent(in) :: dict_size
    end subroutine log_metric_c
  end interface

  interface
    subroutine commit_metrics_c(metrics_name) bind(C, name="commit_metrics")
      use iso_c_binding, only : c_char
      character(kind=c_char), intent(in) :: metrics_name(*)
    end subroutine commit_metrics_c
  end interface

  interface
    subroutine cmf_finalize() bind(C)
    end subroutine cmf_finalize
  end interface

  type, public :: cmf_type

    contains

    procedure :: initialize
    procedure :: initialized
    procedure :: log_metric
    procedure :: commit_metrics
    procedure :: finalize

  end type cmf_type

contains

  !> Initialize CMF with parameters
  subroutine initialize(self, mlmd_path, pipeline_name, context_name, execution_name)
    class(cmf_type), intent(in) :: self
    character(len=*), intent(in) :: mlmd_path, pipeline_name, context_name, execution_name

    if (.not. self%initialized()) then
      call cmf_init(trim(mlmd_path)//c_null_char, trim(pipeline_name)//c_null_char, &
                    trim(context_name)//c_null_char, trim(execution_name)//c_null_char)
    end if

  end subroutine initialize

  !> Check if CMF is initialized
  logical function initialized(self)
    class(cmf_type), intent(in) :: self

    initialized = is_cmf_initialized() == 1
  end function initialized

  !> Log a metric with a key and dictionary of values (key-value pairs)
  subroutine log_metric(self, key, dict_keys, dict_values)
    class(cmf_type),                intent(in) :: self
    character(len=*),               intent(in) :: key
    character(len=*), dimension(:), intent(in) :: dict_keys, dict_values

    integer :: i
    integer(kind=c_int) :: dict_size
    character(kind=c_char, len=C_MAX_STRING), allocatable, target :: c_keys(:), c_values(:)
    type(c_ptr), dimension(:), target, allocatable :: c_keys_ptr, c_values_ptr

    dict_size = size(dict_keys)
    call convert_char_array_to_c(dict_keys, dict_size, c_keys, c_keys_ptr)
    call convert_char_array_to_c(dict_values, dict_size, c_values, c_values_ptr)
    call log_metric_c(trim(key)//c_null_char, c_keys_ptr, c_values_ptr, dict_size)

    if(allocated(c_keys)) deallocate(c_keys)
    if(allocated(c_values)) deallocate(c_values)

  end subroutine log_metric

  !> Commit metrics with a given name
  subroutine commit_metrics(self, metrics_name)
    class(cmf_type), intent(in) :: self
    character(len=*), intent(in) :: metrics_name

    call commit_metrics_c(trim(metrics_name)//c_null_char)

  end subroutine commit_metrics

  !> Finalize CMF and clean up resources
  subroutine finalize(self)
    class(cmf_type), intent(in) :: self

    call cmf_finalize()

  end subroutine finalize

  !> Returns pointers to the start of each string and lengths for each string in a Fortran character array
  subroutine convert_char_array_to_c(character_array_f, n_strings, character_array_c, string_ptrs)
  !> The 2D Fortran character array
  character(len=*),             dimension(:),                       intent(in   ) :: character_array_f
  !> The length of each string
  integer(kind=c_int),                                              intent(in   ) :: n_strings
  !> The character array converted to c_character types
  character(kind=c_char, len=C_MAX_STRING), dimension(:), allocatable, target, intent(  out) :: character_array_c
  !> C-style pointers to the start of each string
  type(c_ptr),                   dimension(:), allocatable,         intent(  out) :: string_ptrs

  integer :: max_length, length
  integer(kind=c_size_t) :: i

  ! Find the size of the 2D array and allocate some of the 1D arrays
  allocate(string_ptrs(n_strings))

  ! Need to find the length of the string, so we can allocate the c_array
  max_length = 0
  do i=1,n_strings
    length = len_trim(character_array_f(i))
    max_length = max(max_length, length)
  enddo

  allocate(character_array_c(n_strings))

  ! Copy the character into a c_char and create pointers to each of the strings
  do i=1,n_strings
    character_array_c(i) = TRIM(character_array_f(i))//c_null_char
    string_ptrs(i) = c_loc(character_array_c(i))
  enddo

end subroutine convert_char_array_to_c

end module cmflib
